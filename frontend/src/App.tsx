import { useState } from "react"

type Message = {
  role: "user" | "assistant"
  content: string
}

type Source = {
  title: string
  url: string
}

type ResearchResponse = {
  thread_id: string
  topic: string
  answer: string
  sources: Source[]
  tools_used: string[]
  execution_time: number
}

type PendingEmail = {
  recipient: string
  subject: string
  body: string
}

type PendingEmailResponse = {
  pending: boolean
  email: PendingEmail | null
}

function App() {
  const [topic, setTopic] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)

  const [sources, setSources] = useState<Source[]>([])
  const [toolsUsed, setToolsUsed] = useState<string[]>([])
  const [executionTime, setExecutionTime] =
    useState<number | null>(null)
  const [report, setReport] = useState("")

  const [threadId, setThreadId] =
    useState<string | null>(null)

  const [feedback, setFeedback] = useState<
    "positive" | "negative" | null
  >(null)

  const [pendingEmail, setPendingEmail] =
    useState<PendingEmail | null>(null)

  const [emailLoading, setEmailLoading] =
    useState(false)

  const checkPendingEmail = async (
    currentThreadId: string,
  ) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/email/pending/${currentThreadId}`,
      )

      if (!response.ok) {
        throw new Error(
          "Failed to check pending email",
        )
      }

      const data: PendingEmailResponse =
        await response.json()

      setPendingEmail(
        data.pending ? data.email : null,
      )
    } catch (error) {
      console.error(error)
    }
  }

  const handleResearch = async () => {
    const trimmedTopic = topic.trim()

    if (!trimmedTopic || loading) {
      return
    }

    setLoading(true)

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: trimmedTopic,
      },
    ])

    setTopic("")
    setSources([])
    setToolsUsed([])
    setExecutionTime(null)
    setReport("")
    setFeedback(null)
    setPendingEmail(null)

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/research",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            topic: trimmedTopic,
            thread_id: threadId,
          }),
        },
      )

      if (!response.ok) {
        throw new Error(
          "Backend request failed",
        )
      }

      const data: ResearchResponse =
        await response.json()

      setThreadId(data.thread_id)

      checkPendingEmail(data.thread_id)

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.answer,
        },
      ])

      setSources(data.sources)
      setToolsUsed(data.tools_used)
      setExecutionTime(data.execution_time)
      setReport(data.answer)
    } catch (error) {
      console.error(error)

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "حدث خطأ أثناء الاتصال بالـ Backend.",
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (
    selectedFeedback:
      | "positive"
      | "negative",
  ) => {
    if (!threadId) {
      return
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/feedback",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            thread_id: threadId,
            feedback: selectedFeedback,
          }),
        },
      )

      if (!response.ok) {
        throw new Error(
          "Feedback request failed",
        )
      }

      const data = await response.json()

      if (data.success) {
        setFeedback(selectedFeedback)
      }
    } catch (error) {
      console.error(error)
    }
  }

  const handleEmailApproval = async (
    approved: boolean,
  ) => {
    if (!threadId || !pendingEmail) {
      return
    }

    setEmailLoading(true)

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/email/approval",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            thread_id: threadId,
            approved,
          }),
        },
      )

      if (!response.ok) {
        throw new Error(
          "Email approval request failed",
        )
      }

      const data = await response.json()

      if (data.success) {
        setPendingEmail(null)

        setMessages((current) => [
          ...current,
          {
            role: "assistant",
            content: data.message,
          },
        ])
      }
    } catch (error) {
      console.error(error)
    } finally {
      setEmailLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Research Assistant</h1>
          <p>
            AI-powered research and analysis
          </p>
        </div>
      </header>

      <main className="container">
        <section className="research-input">
          <label htmlFor="topic">
            Research Topic
          </label>

          <div className="input-row">
            <input
              id="topic"
              type="text"
              value={topic}
              onChange={(event) =>
                setTopic(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleResearch()
                }
              }}
              placeholder="Enter a topic to research..."
              disabled={loading}
            />

            <button
              onClick={handleResearch}
              disabled={
                loading || !topic.trim()
              }
            >
              {loading
                ? "Researching..."
                : "Start Research"}
            </button>
          </div>
        </section>

        <section className="dashboard">
          <div className="chat-panel panel">
            <h2>Chat</h2>

            <div className="chat-messages">
              {messages.length === 0 ? (
                <div className="empty-state">
                  <p>
                    Start a research topic to begin.
                  </p>
                </div>
              ) : (
                messages.map(
                  (message, index) => (
                    <div
                      key={index}
                      className={`message ${message.role}`}
                    >
                      <strong>
                        {message.role ===
                        "user"
                          ? "You"
                          : "Agent"}
                      </strong>

                      <p>
                        {message.content}
                      </p>
                    </div>
                  ),
                )
              )}

              {loading && (
                <div className="message assistant">
                  <strong>Agent</strong>
                  <p>Researching...</p>
                </div>
              )}
            </div>
          </div>

          <div className="sources-panel panel">
            <h2>Sources</h2>

            {sources.length === 0 ? (
              <div className="empty-state">
                <p>No sources yet.</p>
              </div>
            ) : (
              <div className="sources-list">
                {sources.map(
                  (source, index) => (
                    <div
                      className="source-item"
                      key={index}
                    >
                      <strong>
                        {source.title}
                      </strong>

                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Open source
                      </a>
                    </div>
                  ),
                )}
              </div>
            )}
          </div>

          <div className="report-panel panel">
            <h2>Final Report</h2>

            {report ? (
              <div className="report-content">
                <p>{report}</p>
              </div>
            ) : (
              <div className="empty-state">
                <p>
                  Your final research report
                  will appear here.
                </p>
              </div>
            )}
          </div>

          <div className="details-panel panel">
            <h2>Agent Details</h2>

            <div className="detail-item">
              <span>Tools Used</span>

              <strong>
                {toolsUsed.length > 0
                  ? toolsUsed.join(", ")
                  : "—"}
              </strong>
            </div>

            <div className="detail-item">
              <span>Execution Time</span>

              <strong>
                {executionTime !== null
                  ? `${executionTime} seconds`
                  : "—"}
              </strong>
            </div>

            <div className="feedback">
              <span>Feedback</span>

              <div className="feedback-buttons">
                <button
                  onClick={() =>
                    handleFeedback("positive")
                  }
                  disabled={!threadId}
                  style={{
                    opacity:
                      feedback === "positive"
                        ? 1
                        : 0.6,
                  }}
                >
                  👍
                </button>

                <button
                  onClick={() =>
                    handleFeedback("negative")
                  }
                  disabled={!threadId}
                  style={{
                    opacity:
                      feedback === "negative"
                        ? 1
                        : 0.6,
                  }}
                >
                  👎
                </button>
              </div>
            </div>
          </div>

          {pendingEmail && (
            <div className="panel email-approval-panel">
              <h2>Email Approval</h2>

              <p>
                The research report is ready
                to be sent by email.
              </p>

              <div className="email-details">
                <p>
                  <strong>To:</strong>{" "}
                  {pendingEmail.recipient}
                </p>

                <p>
                  <strong>Subject:</strong>{" "}
                  {pendingEmail.subject}
                </p>
              </div>

              <div className="email-approval-buttons">
                <button
                  onClick={() =>
                    handleEmailApproval(true)
                  }
                  disabled={emailLoading}
                >
                  {emailLoading
                    ? "Processing..."
                    : "Approve"}
                </button>

                <button
                  onClick={() =>
                    handleEmailApproval(false)
                  }
                  disabled={emailLoading}
                >
                  Reject
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App