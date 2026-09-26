import { useEffect, useState } from "react";
import "./App.css";

const CRYPTO_GUARD_URL =
  import.meta.env.VITE_CRYPTO_GUARD_URL || "http://localhost:5173";

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

function App() {
  const [requests, setRequests] = useState<InvestigationRequest[]>([]);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (
        event.origin !==
        CRYPTO_GUARD_URL.replace(/\/$/, "")
      ) {
        return;
      }

      const data = event.data as Partial<IncomingRequest> & {
        type?: string;
      };

      if (
        !data ||
        data.type !== "CRYPTO_GUARD_INVESTIGATION_REQUEST" ||
        typeof data.caseId !== "string" ||
        !(data.pdfBuffer instanceof ArrayBuffer)
      ) {
        return;
      }

      const newRequest: InvestigationRequest = {
        id: crypto.randomUUID(),
        caseId: data.caseId,
        receivedAt: new Date().toLocaleString("en-IN", {
          dateStyle: "medium",
          timeStyle: "short",
        }),
        status: "pending",
        pdfData: data.pdfBuffer,
        filename:
          data.filename || "Investigation Report.pdf",
      };

      setRequests((current) => [newRequest, ...current]);
    };

    window.addEventListener("message", handleMessage);

    /*
     * Tell the Crypto Guard window that this portal
     * has finished loading and is ready to receive
     * the investigation report.
     */
    if (window.opener) {
      window.opener.postMessage(
        {
          type: "CRYPTO_GUARD_DEMO_PORTAL_READY",
        },
        CRYPTO_GUARD_URL.replace(/\/$/, ""),
      );
    }

    return () => {
      window.removeEventListener("message", handleMessage);
    };
  }, []);

  const acceptRequest = (id: string) => {
    setRequests((current) =>
      current.map((request) =>
        request.id === id
          ? { ...request, status: "accepted" }
          : request,
      ),
    );
  };

  const viewReport = (request: InvestigationRequest) => {
    if (!request.pdfData) {
      alert("Investigation report is not available.");
      return;
    }

    try {
      const blob = new Blob([request.pdfData], {
        type: "application/pdf",
      });

      const url = URL.createObjectURL(blob);

      window.open(url, "_blank", "noopener,noreferrer");

      window.setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 60000);
    } catch {
      alert("Unable to open the investigation report.");
    }
  };

  const pendingCount = requests.filter(
    (request) => request.status === "pending",
  ).length;

  return (
    <div className="portal">
      <header className="portal-header">
        <div className="brand">
          <div className="brand-mark">S</div>

          <div>
            <div className="brand-title">SAHYOG</div>

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
          <div className="eyebrow">CRYPTO GUARD V2</div>

          <h1>Investigation Requests</h1>

          <p>
            Incoming cryptocurrency investigation reports received
            from Crypto Guard V2.
          </p>
        </section>

        <section className="warning-banner">
          <div className="warning-icon">!</div>

          <div>
            <strong>Demonstration Environment</strong>

            <p>
              This portal is a simulated presentation workflow.
              It is not an official SAHYOG, MHA, VASP, or
              law-enforcement response system.
            </p>
          </div>
        </section>

        <section className="queue-header">
          <div>
            <span className="section-label">
              INCOMING QUEUE
            </span>

            <h2>Recent Investigation Requests</h2>
          </div>

          <div className="queue-count">
            <strong>{pendingCount}</strong>

            <span>Pending</span>
          </div>
        </section>

        {requests.length === 0 ? (
          <section className="empty-state">
            <div className="empty-icon">↓</div>

            <h3>No investigation requests</h3>

            <p>
              Requests sent from Crypto Guard V2 will appear here.
            </p>
          </section>
        ) : (
          <section className="request-list">
            {requests.map((request) => (
              <article
                className={`request-card ${
                  request.status === "accepted"
                    ? "request-accepted"
                    : ""
                }`}
                key={request.id}
              >
                <div className="request-top">
                  <div className="notification-icon">
                    {request.status === "accepted"
                      ? "✓"
                      : "!"}
                  </div>

                  <div className="request-heading">
                    <div className="request-title">
                      {request.status === "accepted"
                        ? "Investigation Request Accepted"
                        : "New Investigation Request"}
                    </div>

                    <div className="request-time">
                      Received {request.receivedAt}
                    </div>
                  </div>

                  <span
                    className={`request-status ${
                      request.status === "accepted"
                        ? "accepted"
                        : "pending"
                    }`}
                  >
                    {request.status === "accepted"
                      ? "ACCEPTED"
                      : "PENDING"}
                  </span>
                </div>

                <div className="request-body">
                  <div className="case-information">
                    <span>CASE ID</span>

                    <strong>{request.caseId}</strong>
                  </div>

                  <div className="report-information">
                    <div className="pdf-icon">PDF</div>

                    <div>
                      <strong>{request.filename}</strong>

                      <span>
                        Investigation report generated by
                        Crypto Guard V2
                      </span>
                    </div>
                  </div>
                </div>

                <div className="request-actions">
                  <button
                    className="secondary-button"
                    onClick={() => viewReport(request)}
                    disabled={!request.pdfData}
                  >
                    View Report
                  </button>

                  {request.status === "pending" ? (
                    <button
                      className="submit-button"
                      onClick={() =>
                        acceptRequest(request.id)
                      }
                    >
                      Accept Request

                      <span>→</span>
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
        <span>Crypto Guard V2</span>
        <span>Demo Investigation Portal</span>
        <span>Simulation Only</span>
      </footer>
    </div>
  );
}

export default App;