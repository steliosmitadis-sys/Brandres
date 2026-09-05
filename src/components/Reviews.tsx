import { reviews, reviewsHeadline, type Review } from "../data/content";

function Stars({ rating }: { rating: number }) {
  return (
    <span
      className="text-[13px] tracking-[0.2em] text-accent"
      aria-label={`${rating} στα 5`}
    >
      <span aria-hidden>{"★".repeat(rating)}</span>
    </span>
  );
}

function ReviewCard({ review }: { review: Review }) {
  return (
    <figure className="flex h-full flex-col border border-line bg-surface p-6 sm:p-7">
      <Stars rating={review.rating} />
      <blockquote className="mt-4 text-[15px] leading-relaxed">
        {review.review}
      </blockquote>
      <figcaption className="mt-5 border-t border-line pt-4 text-[14px]">
        <span className="font-medium">{review.name}</span>
        <span className="text-muted"> — {review.city}</span>
      </figcaption>
    </figure>
  );
}

export function Reviews() {
  return (
    <section id="reviews" className="border-b border-line">
      <div className="mx-auto max-w-[1180px] px-5 py-20 sm:px-8 sm:py-24">
        <h2 className="max-w-[18ch] text-[32px] font-semibold sm:text-[44px]">
          {reviewsHeadline}
        </h2>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {reviews.map((review) => (
            <ReviewCard key={review.name} review={review} />
          ))}
        </div>
      </div>
    </section>
  );
}
