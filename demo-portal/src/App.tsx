import { useEffect, useState } from "react";
import "./App.css";

const CRYPTO_GUARD_URL =
  import.meta.env.VITE_CRYPTO_GUARD_URL || "http://localhost:5173";

const DB_NAME = "crypto-guard-demo-portal";
const DB_VERSION = 2;
const STORE_NAME = "investigation-requests";

type RequestStatus = "pending" | "accepted";

type InvestigationRequest = {
  id: string;
  caseId: string;
  receivedAt: string;
  status: RequestStatus;
  pdfData?: ArrayBuffer;
  filename: string;
};

type IncomingRequest = {
  type: "CRYPTO_GUARD_INVESTIGATION_REQUEST";
  caseId: string;
  filename: string;
  pdfBuffer: ArrayBuffer;
};

/* ============================================================
   INDEXEDDB
   ============================================================ */

function openRequestDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) {
      reject(
        new Error(
          "IndexedDB is not available in this browser.",
        ),
      );
      return;
    }

    const request = indexedDB.open(
      DB_NAME,
      DB_VERSION,
    );

    request.onerror = () => {
      reject(
        request.error ||
          new Error(
            "Unable to open investigation request database.",
          ),
      );
    };

    request.onupgradeneeded = () => {
      const database = request.result;

      if (
        !database.objectStoreNames.contains(
          STORE_NAME,
        )
      ) {
        database.createObjectStore(STORE_NAME, {
          keyPath: "id",
        });
      }
    };

    request.onsuccess = () => {
      const database = request.result;

      database.onversionchange = () => {
        database.close();
      };

      resolve(database);
    };
  });
}

async function saveInvestigationRequest(
  investigationRequest: InvestigationRequest,
): Promise<void> {
  const database =
    await openRequestDatabase();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction(
      STORE_NAME,
      "readwrite",
    );

    const store =
      transaction.objectStore(STORE_NAME);

    store.put(investigationRequest);

    transaction.oncomplete = () => {
      database.close();
      resolve();
    };

    transaction.onerror = () => {
      database.close();

      reject(
        transaction.error ||
          new Error(
            "Unable to save investigation request.",
          ),
      );
    };

    transaction.onabort = () => {
      database.close();

      reject(
        transaction.error ||
          new Error(
            "Investigation request save was aborted.",
          ),
      );
    };
  });
}

async function loadInvestigationRequests(): Promise<
  InvestigationRequest[]
> {
  const database =
    await openRequestDatabase();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction(
      STORE_NAME,
      "readonly",
    );

    const store =
      transaction.objectStore(STORE_NAME);

    const request = store.getAll();

    request.onsuccess = () => {
      database.close();

      const requests =
        (request.result as InvestigationRequest[]) ||
        [];

      requests.sort(
        (a, b) =>
          new Date(b.receivedAt).getTime() -
          new Date(a.receivedAt).getTime(),
      );

      resolve(requests);
    };

    request.onerror = () => {
      database.close();

      reject(
        request.error ||
          new Error(
            "Unable to load investigation requests.",
          ),
      );
    };
  });
}

async function updateInvestigationRequest(
  investigationRequest: InvestigationRequest,
): Promise<void> {
  await saveInvestigationRequest(
    investigationRequest,
  );
}

/* ============================================================
   APP
   ============================================================ */

function App() {
  const [requests, setRequests] = useState<
    InvestigationRequest[]
  >([]);

  const [databaseReady, setDatabaseReady] =
    useState(false);

  const [databaseError, setDatabaseError] =
    useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    /*
     * First restore all previously received
     * investigation requests.
     *
     * The message listener is intentionally
     * registered only after IndexedDB restoration
     * completes. This prevents an incoming request
     * from being overwritten by an older database
     * load.
     */
    const initializePortal = async () => {
      try {
        const savedRequests =
          await loadInvestigationRequests();

        if (cancelled) {
          return;
        }

        setRequests(savedRequests);
        setDatabaseReady(true);
        setDatabaseError(null);
      } catch (error) {
        console.error(
          "Failed to initialize investigation request database:",
          error,
        );

        if (cancelled) {
          return;
        }

        setDatabaseReady(true);
        setDatabaseError(
          "Local request storage is unavailable. Requests may not survive a refresh.",
        );
      }
    };

    void initializePortal();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    /*
     * Do not start accepting investigation
     * requests until the initial IndexedDB restore
     * has completed.
     */
    if (!databaseReady) {
      return;
    }

    const handleMessage = (
      event: MessageEvent,
    ) => {
      /*
       * Only accept messages from the configured
       * Crypto Guard V2 origin.
       */
      if (
        event.origin !==
        CRYPTO_GUARD_URL.replace(/\/$/, "")
      ) {
        return;
      }

      const data =
        event.data as Partial<IncomingRequest> & {
          type?: string;
        };

      /*
       * Validate the incoming investigation request.
       */
      if (
        !data ||
        data.type !==
          "CRYPTO_GUARD_INVESTIGATION_REQUEST" ||
        typeof data.caseId !== "string" ||
        !(data.pdfBuffer instanceof ArrayBuffer)
      ) {
        return;
      }

      /*
       * Store the timestamp as ISO so sorting
       * remains reliable after refresh.
       */
      const newRequest: InvestigationRequest = {
        id: crypto.randomUUID(),
        caseId: data.caseId,
        receivedAt: new Date().toISOString(),
        status: "pending",
        pdfData: data.pdfBuffer,
        filename:
          data.filename ||
          "Investigation Report.pdf",
      };

      /*
       * Persist the complete request first.
       * Only show it in the UI after IndexedDB
       * confirms that the write succeeded.
       */
      void saveInvestigationRequest(
        newRequest,
      )
        .then(() => {
          setRequests((current) => [
            newRequest,
            ...current,
          ]);
        })
        .catch((error) => {
          console.error(
            "Failed to save investigation request:",
            error,
          );

          alert(
            "The investigation request was received, but could not be saved locally.",
          );
        });
    };

    window.addEventListener(
      "message",
      handleMessage,
    );

    /*
     * Tell the Crypto Guard window that this portal
     * has finished loading and is ready to receive
     * the investigation report.
     */
    if (window.opener) {
      window.opener.postMessage(
        {
          type:
            "CRYPTO_GUARD_DEMO_PORTAL_READY",
        },
        CRYPTO_GUARD_URL.replace(/\/$/, ""),
      );
    }

    return () => {
      window.removeEventListener(
        "message",
        handleMessage,
      );
    };
  }, [databaseReady]);

  /*
   * Accept an investigation request and persist
   * the new status in IndexedDB.
   */
  const acceptRequest = (id: string) => {
    setRequests((current) => {
      const updated = current.map(
        (request) =>
          request.id === id
            ? {
                ...request,
                status:
                  "accepted" as const,
              }
            : request,
      );

      const acceptedRequest =
        updated.find(
          (request) => request.id === id,
        );

      if (acceptedRequest) {
        void updateInvestigationRequest(
          acceptedRequest,
        ).catch((error) => {
          console.error(
            "Failed to persist accepted investigation request:",
            error,
          );
        });
      }

      return updated;
    });
  };

  /*
   * Open the persisted investigation report PDF.
   */
  const viewReport = (
    request: InvestigationRequest,
  ) => {
    if (!request.pdfData) {
      alert(
        "Investigation report is not available.",
      );
      return;
    }

    try {
      const blob = new Blob(
        [request.pdfData],
        {
          type: "application/pdf",
        },
      );

      const url =
        URL.createObjectURL(blob);

      window.open(
        url,
        "_blank",
        "noopener,noreferrer",
      );

      window.setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 60000);
    } catch {
      alert(
        "Unable to open the investigation report.",
      );
    }
  };

  const pendingCount =
    requests.filter(
      (request) =>
        request.status === "pending",
    ).length;

  return (
    <div className="portal">
      <header className="portal-header">
        <div className="brand">
          <div className="brand-mark">
            S
          </div>

          <div>
            <div className="brand-title">
              SAHYOG
            </div>

            <div className="brand-subtitle">
              Investigation Request Portal
            </div>
          </div>
        </div>

        <div className="demo-badge">
          DEMO / SIMULATION
        </div>
      </header>

      <main className="portal-main">
        <section className="hero">
          <div className="eyebrow">
            CRYPTO GUARD V2
          </div>

          <h1>
            Investigation Requests
          </h1>

          <p>
            Incoming cryptocurrency
            investigation reports received
            from Crypto Guard V2.
          </p>
        </section>

        <section className="warning-banner">
          <div className="warning-icon">
            !
          </div>

          <div>
            <strong>
              Demonstration Environment
            </strong>

            <p>
              This portal is a simulated
              presentation workflow. It is not
              an official SAHYOG, MHA, VASP, or
              law-enforcement response system.
            </p>
          </div>
        </section>

        {databaseError && (
          <section
            style={{
              marginTop: "14px",
              padding: "12px 14px",
              border: "1px solid #d9a441",
              borderRadius: "8px",
              background:
                "rgba(217, 164, 65, 0.08)",
              color: "#8a6419",
              fontSize: "13px",
              fontWeight: 700,
              lineHeight: 1.45,
            }}
          >
            {databaseError}
          </section>
        )}

        <section className="queue-header">
          <div>
            <span className="section-label">
              INCOMING QUEUE
            </span>

            <h2>
              Recent Investigation Requests
            </h2>
          </div>

          <div className="queue-count">
            <strong>
              {pendingCount}
            </strong>

            <span>
              Pending
            </span>
          </div>
        </section>

        {requests.length === 0 ? (
          <section className="empty-state">
            <div className="empty-icon">
              ↓
            </div>

            <h3>
              No investigation requests
            </h3>

            <p>
              Requests sent from Crypto Guard V2
              will appear here.
            </p>
          </section>
        ) : (
          <section className="request-list">
            {requests.map((request) => (
              <article
                className={`request-card ${
                  request.status ===
                  "accepted"
                    ? "request-accepted"
                    : ""
                }`}
                key={request.id}
              >
                <div className="request-top">
                  <div className="notification-icon">
                    {request.status ===
                    "accepted"
                      ? "✓"
                      : "!"}
                  </div>

                  <div className="request-heading">
                    <div className="request-title">
                      {request.status ===
                      "accepted"
                        ? "Investigation Request Accepted"
                        : "New Investigation Request"}
                    </div>

                    <div className="request-time">
                      Received{" "}
                      {new Date(
                        request.receivedAt,
                      ).toLocaleString(
                        "en-IN",
                        {
                          dateStyle:
                            "medium",
                          timeStyle:
                            "short",
                        },
                      )}
                    </div>
                  </div>

                  <span
                    className={`request-status ${
                      request.status ===
                      "accepted"
                        ? "accepted"
                        : "pending"
                    }`}
                  >
                    {request.status ===
                    "accepted"
                      ? "ACCEPTED"
                      : "PENDING"}
                  </span>
                </div>

                <div className="request-body">
                  <div className="case-information">
                    <span>
                      CASE ID
                    </span>

                    <strong>
                      {request.caseId}
                    </strong>
                  </div>

                  <div className="report-information">
                    <div className="pdf-icon">
                      PDF
                    </div>

                    <div>
                      <strong>
                        {request.filename}
                      </strong>

                      <span>
                        Investigation report
                        generated by Crypto
                        Guard V2
                      </span>
                    </div>
                  </div>
                </div>

                <div className="request-actions">
                  <button
                    className="secondary-button"
                    onClick={() =>
                      viewReport(request)
                    }
                    disabled={
                      !request.pdfData
                    }
                  >
                    View Report
                  </button>

                  {request.status ===
                  "pending" ? (
                    <button
                      className="submit-button"
                      onClick={() =>
                        acceptRequest(
                          request.id,
                        )
                      }
                    >
                      Accept Request

                      <span>
                        →
                      </span>
                    </button>
                  ) : (
                    <div className="accepted-message">
                      ✓ Request accepted
                    </div>
                  )}
                </div>
              </article>
            ))}
          </section>
        )}
      </main>

      <footer className="portal-footer">
        <span>
          Crypto Guard V2
        </span>

        <span>
          Demo Investigation Portal
        </span>

        <span>
          Simulation Only
        </span>
      </footer>
    </div>
  );
}

export default App;