import { contactEmail, finalCta } from "../data/content";

export function FinalCta() {
  return (
    <section id="contact" className="bg-ink text-background">
      <div className="mx-auto max-w-[1180px] px-5 py-20 sm:px-8 sm:py-28">
        <h2 className="max-w-[20ch] text-[32px] font-semibold text-background sm:text-[48px]">
          {finalCta.headline}
        </h2>
        <p className="mt-5 max-w-[52ch] text-[17px] leading-relaxed text-background/70">
          {finalCta.description}
        </p>
        <a
          href={`mailto:${contactEmail}`}
          className="mt-10 inline-flex items-center justify-center bg-accent px-7 py-4 text-[15px] font-medium text-background transition-opacity hover:opacity-90"
        >
          {finalCta.cta}
        </a>
      </div>
    </section>
  );
}
