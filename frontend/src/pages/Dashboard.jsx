import { useEffect, useState } from "react";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import { getDashboard } from "../api/dashboard";

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Legend, Tooltip);

function StatCard({ label, value }) {
  return (
    <div className="auth-card" style={{ padding: "1.25rem 1.5rem", textAlign: "center" }}>
      <p style={{ opacity: 0.7, margin: "0 0 0.25rem", fontSize: "0.85rem" }}>{label}</p>
      <p style={{ margin: 0, fontSize: "1.8rem", fontWeight: 700 }}>{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => setError("Could not load your dashboard."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ padding: "3rem 0" }}>Loading your dashboard...</div>;
  if (error) return <div className="container" style={{ padding: "3rem 0" }}><p className="auth-error" role="alert">{error}</p></div>;
  if (!data) return null;

  const { totals, posts } = data;

  // Bar chart — likes vs comments per post (the required "distribution of
  // likes/comments per post" visualization).
  const perPostBarData = {
    labels: posts.map((p) => (p.title.length > 20 ? `${p.title.slice(0, 20)}…` : p.title)),
    datasets: [
      {
        label: "Likes",
        data: posts.map((p) => p.likes),
        backgroundColor: "#4f8ef7",
      },
      {
        label: "Comments",
        data: posts.map((p) => p.comments),
        backgroundColor: "#f7a94f",
      },
    ],
  };

  // Line chart (optional, per the brief) — post activity over time, using
  // each post's own like+comment+view count plotted against its creation date.
  const sortedByDate = [...posts].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  const activityLineData = {
    labels: sortedByDate.map((p) => new Date(p.created_at).toLocaleDateString()),
    datasets: [
      {
        label: "Engagement per post (likes + comments + views)",
        data: sortedByDate.map((p) => p.likes + p.comments + p.views),
        borderColor: "#4f8ef7",
        backgroundColor: "rgba(79, 142, 247, 0.2)",
        tension: 0.3,
        fill: true,
      },
    ],
  };

  return (
    <section className="section">
      <div className="container">
        <header className="section-header">
          <p className="section-label">Your Activity</p>
          <h2>Dashboard</h2>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          <StatCard label="Posts Created" value={totals.total_posts} />
          <StatCard label="Comments Made" value={totals.total_comments_made} />
          <StatCard label="Likes Received" value={totals.total_likes_received} />
          <StatCard label="Total Post Views" value={totals.total_views} />
        </div>

        {posts.length === 0 ? (
          <p>You haven't created any posts yet — your charts will appear here once you do.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            <div className="auth-card" style={{ padding: "1.5rem" }}>
              <h3 style={{ marginTop: 0 }}>Likes &amp; Comments per Post</h3>
              <Bar
                data={perPostBarData}
                options={{
                  responsive: true,
                  plugins: { legend: { position: "top" } },
                  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                }}
              />
            </div>

            <div className="auth-card" style={{ padding: "1.5rem" }}>
              <h3 style={{ marginTop: 0 }}>Post Activity Over Time</h3>
              <Line
                data={activityLineData}
                options={{
                  responsive: true,
                  plugins: { legend: { position: "top" } },
                  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                }}
              />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}