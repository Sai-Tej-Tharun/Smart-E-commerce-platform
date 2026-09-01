import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="container" style={{ padding: "5rem 0", textAlign: "center" }}>
      <h1>404</h1>
      <p>Page not found.</p>
      <Link to="/" className="btn btn-primary">Back Home</Link>
    </div>
  );
}
