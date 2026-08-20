import { Link } from "react-router-dom";

export default function ProductCard({ product, onAddToCart, adding }) {
  const image = product.images?.[0];

  return (
    <article className="product-card" aria-label={product.name}>
      <div className="product-card__image">
        {image ? (
          <img src={image} alt={product.name} loading="lazy" />
        ) : (
          <div className="product-card__image-placeholder" aria-hidden="true" />
        )}
        {product.stock === 0 && (
          <div className="product-card__badge"><span className="badge badge-error">Out of stock</span></div>
        )}
      </div>
      <div className="product-card__body">
        {product.category && <p className="product-card__category">{product.category}</p>}
        <h3 className="product-card__title">
          <Link to={`/products/${product.id}`}>{product.name}</Link>
        </h3>
        <div className="product-card__price">
          <span className="product-card__price-current">₹{Number(product.price).toFixed(2)}</span>
        </div>
      </div>
      <div className="product-card__footer">
        <button
          className="btn btn-primary w-full"
          disabled={product.stock === 0 || adding}
          onClick={() => onAddToCart?.(product)}
        >
          {product.stock === 0 ? "Out of stock" : adding ? "Adding..." : "Add to Cart"}
        </button>
      </div>
    </article>
  );
}
