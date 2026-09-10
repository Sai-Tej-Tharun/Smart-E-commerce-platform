// Displays a static star rating (read-only) — used on product cards, the
// product detail page, and each review in the list. `value` is 0-5 and
// can be fractional (e.g. 4.3 from an average); stars render as
// filled/half/empty accordingly. `count`, if given, appends "(N)" —
// pass it for the "total reviews" part of the Rating Aggregation requirement.
export default function StarRating({ value, count, size = "1rem" }) {
  if (value === null || value === undefined) {
    return <span style={{ fontSize: size, opacity: 0.6 }}>No reviews yet</span>;
  }

  const stars = [1, 2, 3, 4, 5].map((n) => {
    if (value >= n) return "★";
    if (value >= n - 0.5) return "⯨"; // half star
    return "☆";
  });

  return (
    <span aria-label={`${value} out of 5 stars${count !== undefined ? ` (${count} review${count === 1 ? "" : "s"})` : ""}`} style={{ fontSize: size, color: "var(--color-accent, #c9a26d)", whiteSpace: "nowrap" }}>
      {stars.join("")}
      {count !== undefined && (
        <span style={{ color: "inherit", opacity: 0.7, fontSize: "0.85em", marginLeft: "0.35em" }}>
          {value.toFixed(1)} ({count})
        </span>
      )}
    </span>
  );
}