// Shared publish-options control for the Create and Edit post pages.
// value = { option: "publish" | "draft" | "schedule", date: "YYYY-MM-DD", time: "HH:mm" }

const pad = (n) => String(n).padStart(2, "0");

const todayLocal = () => {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

// UTC ISO string from the API -> local date/time inputs
export const toLocalParts = (iso) => {
  const d = new Date(iso);
  return {
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    time: `${pad(d.getHours())}:${pad(d.getMinutes())}`,
  };
};

// Returns an error message, or "" when the choice is valid.
export const validatePublish = ({ option, date, time }) => {
  if (option !== "schedule") return "";
  if (!date || !time) return "Please pick both a date and a time for the scheduled post.";
  if (new Date(`${date}T${time}`) <= new Date()) return "The scheduled time must be in the future.";
  return "";
};

// Adds publish_option (+ scheduled_at as a UTC ISO string) to the FormData.
export const appendPublishFields = (formData, { option, date, time }) => {
  formData.append("publish_option", option);
  if (option === "schedule") {
    formData.append("scheduled_at", new Date(`${date}T${time}`).toISOString());
  }
};

export const submitLabel = (option, busy) => {
  if (option === "draft") return busy ? "Saving..." : "Save Draft";
  if (option === "schedule") return busy ? "Scheduling..." : "Schedule Post";
  return busy ? "Publishing..." : "Publish Post";
};

const OPTIONS = [
  { id: "publish", label: "Publish Now" },
  { id: "draft", label: "Save as Draft" },
  { id: "schedule", label: "Schedule Post" },
];

export default function PublishOptions({ value, onChange }) {
  const set = (patch) => onChange({ ...value, ...patch });

  return (
    <div className="auth-field">
      <span className="auth-label">Publish Options</span>

      <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap", marginTop: "0.4rem" }}>
        {OPTIONS.map((o) => (
          <label key={o.id} style={{ display: "flex", alignItems: "center", gap: "0.4rem", cursor: "pointer" }}>
            <input
              type="radio"
              name="publishOption"
              value={o.id}
              checked={value.option === o.id}
              onChange={() => set({ option: o.id })}
            />
            {o.label}
          </label>
        ))}
      </div>

      {value.option === "schedule" && (
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginTop: "0.75rem" }}>
          <div style={{ flex: 1, minWidth: "150px" }}>
            <label className="auth-label" htmlFor="scheduleDate">Date</label>
            <input
              type="date"
              id="scheduleDate"
              className="auth-input"
              min={todayLocal()}
              value={value.date}
              onChange={(e) => set({ date: e.target.value })}
            />
          </div>
          <div style={{ flex: 1, minWidth: "150px" }}>
            <label className="auth-label" htmlFor="scheduleTime">Time</label>
            <input
              type="time"
              id="scheduleTime"
              className="auth-input"
              value={value.time}
              onChange={(e) => set({ time: e.target.value })}
            />
          </div>
        </div>
      )}
    </div>
  );
}