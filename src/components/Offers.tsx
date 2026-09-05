import { contactEmail, offers, offersIntro, type Offer } from "../data/content";

function Check() {
  return (
    <svg
      className="mt-[7px] h-3 w-3 shrink-0 text-accent"
      viewBox="0 0 12 12"
      fill="none"
      aria-hidden
    >
      <path
        d="M1.5 6.5 4.5 9.5 10.5 2.5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="square"
      />
    </svg>
  );
}

function OfferBlock({ offer }: { offer: Offer }) {
  const featured = offer.featured === true;

  return (
    <article
      id={offer.id}
      className={
        featured
          ? "border-2 border-ink bg-surface p-6 sm:p-10 lg:p-14"
          : "border border-line bg-surface p-6 sm:p-10 lg:p-12"
      }
    >
      <p
        className={`text-[12px] font-semibold uppercase tracking-[0.16em] ${
          featured ? "text-accent" : "text-muted"
        }`}
      >
        {offer.badge}
      </p>

      <h3
        className={`mt-5 max-w-[20ch] font-semibold ${
          featured
            ? "text-[28px] sm:text-[38px] lg:text-[44px]"
            : "text-[26px] sm:text-[32px] lg:text-[36px]"
        }`}
      >
        {offer.title}
      </h3>

      <p className="mt-5 max-w-[58ch] text-[16px] leading-relaxed text-muted sm:text-[17px]">
        {offer.description}
      </p>

      <div className="mt-10 grid gap-10 lg:grid-cols-2 lg:gap-14">
        <div>
          <h4 className="text-[12px] font-semibold uppercase tracking-[0.16em] text-muted">
            Τι περιλαμβάνει
          </h4>
          <ul className="mt-5 space-y-2.5">
            {offer.features.map((feature) => (
              <li key={feature} className="flex gap-3 text-[15px]">
                <Check />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="text-[12px] font-semibold uppercase tracking-[0.16em] text-muted">
            Πώς δουλεύει
          </h4>
          <ol className="mt-5 space-y-5">
            {offer.howItWorks.map((item) => (
              <li key={item.step} className="flex gap-4">
                <span className="w-7 shrink-0 pt-[3px] text-[13px] font-semibold tabular-nums text-accent">
                  {item.step}
                </span>
                <span>
                  <span className="block text-[15px] font-medium">{item.title}</span>
                  <span className="mt-1 block text-[15px] text-muted">
                    {item.description}
                  </span>
                </span>
              </li>
            ))}
          </ol>
        </div>
      </div>

      <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
      <a
        href={`mailto:${contactEmail}?subject=${encodeURIComponent(offer.cta)}`}
        className={`inline-flex items-center justify-center px-7 py-4 text-[15px] font-medium transition-colors ${
          featured
            ? "bg-ink text-background hover:bg-accent"
            : "border border-ink hover:bg-ink hover:text-background"
        }`}
      >
        {offer.cta}
      </a>

        <a
          href={`${import.meta.env.BASE_URL}diadikasia#${offer.id}`}
          target="_blank"
          rel="noopener"
          className="inline-flex items-center gap-2 px-1 py-4 text-[15px] font-medium text-muted underline decoration-line underline-offset-4 transition-colors hover:text-ink hover:decoration-accent"
        >
          Δες αναλυτικά τη διαδικασία
          <svg className="h-3.5 w-3.5" viewBox="0 0 14 14" fill="none" aria-hidden>
            <path
              d="M5 2h7v7M12 2 3 11M9 12H2V5"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinecap="square"
            />
          </svg>
          <span className="sr-only">(ανοίγει σε νέο παράθυρο)</span>
        </a>
      </div>
    </article>
  );
}

export function Offers() {
  return (
    <section id="offers" className="border-b border-line">
      <div className="mx-auto max-w-[1180px] px-5 py-20 sm:px-8 sm:py-24">
        <h2 className="max-w-[18ch] text-[32px] font-semibold sm:text-[44px]">
          {offersIntro.headline}
        </h2>
        <p className="mt-5 max-w-[54ch] text-[17px] leading-relaxed text-muted">
          {offersIntro.description}
        </p>

        <div className="mt-14 space-y-8 sm:mt-16">
          {offers.map((offer) => (
            <OfferBlock key={offer.id} offer={offer} />
          ))}
        </div>
      </div>
    </section>
  );
}
