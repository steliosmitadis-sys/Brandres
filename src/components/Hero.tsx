import { contactEmail, hero } from "../data/content";

export function Hero() {
  return (
    <section id="top" className="border-b border-line">
      <div className="mx-auto max-w-[1180px] px-5 py-20 sm:px-8 sm:py-28 lg:py-32">
        <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-accent">
          {hero.eyebrow}
        </p>

        <h1 className="mt-6 max-w-[16ch] text-[38px] font-semibold sm:text-[54px] lg:text-[68px]">
          {hero.headline}
        </h1>

        <p className="mt-7 max-w-[52ch] text-[17px] leading-relaxed text-muted sm:text-[19px]">
          {hero.description}
        </p>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <a
            href="#offers"
            className="inline-flex items-center justify-center bg-ink px-7 py-4 text-[15px] font-medium text-background transition-colors hover:bg-accent"
          >
            {hero.primaryCta}
          </a>
          <a
            href={`mailto:${contactEmail}`}
            className="inline-flex items-center justify-center border border-line px-7 py-4 text-[15px] font-medium transition-colors hover:border-ink"
          >
            {hero.secondaryCta}
          </a>
        </div>
      </div>
    </section>
  );
}
