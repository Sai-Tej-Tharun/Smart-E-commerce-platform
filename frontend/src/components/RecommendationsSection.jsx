import ProductCard from "./ProductCard";

// Shared shell for "Recommended For You" (Home), "You May Also Like"
// (Home, trending), and "Similar Products" (ProductDetail) — all three
// just render a ProductOut-shaped list, so one component covers them.
// Renders nothing while products haven't loaded yet or the list is empty,
// so an empty recommendation set never leaves a blank heading on the page.
export default function RecommendationsSection({ title, subtitle, products, onAddToCart, addingId }) {
  if (!products || products.length === 0) return null;

  return (
    <section className="section">
      <div className="container">
        <header className="section-header">
          {subtitle && <p className="section-label">{subtitle}</p>}
          <h2>{title}</h2>
        </header>
        <div className="grid grid-4 products-grid">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} onAddToCart={onAddToCart} adding={addingId === p.id} />
          ))}
        </div>
      </div>
    </section>
  );
}