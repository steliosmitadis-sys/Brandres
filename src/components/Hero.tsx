import { asset, contactEmail, hero } from "../data/content";

export function Hero() {
  return (
    <section id="top" className="border-b border-line">
      <div className="mx-auto grid max-w-[1180px] items-center gap-12 px-5 py-20 sm:px-8 sm:py-24 lg:grid-cols-[1.15fr_1fr] lg:gap-16 lg:py-28">
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-accent">
            {hero.eyebrow}
          </p>

          <h1 className="mt-6 text-[38px] font-semibold sm:text-[50px] lg:text-[56px]">
            {hero.headline}
          </h1>

          <p className="mt-7 max-w-[48ch] text-[17px] leading-relaxed text-muted sm:text-[18px]">
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

        <img
          src={asset(hero.image)}
          alt={hero.imageAlt}
          width={800}
          height={1000}
          className="aspect-[4/5] w-full border border-line object-cover"
        />
      </div>
    </section>
  );
}
