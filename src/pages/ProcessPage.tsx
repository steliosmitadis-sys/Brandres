import { Link } from "react-router-dom";
import {
  mailto,
  processDetails,
  processIntro,
  type ProcessDetail,
} from "../data/content";

function ProcessBlock({ detail }: { detail: ProcessDetail }) {
  return (
    <article id={detail.offerId} className="border-t border-line pt-12">
      <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-accent">
        {detail.badge}
      </p>
      <h2 className="mt-4 max-w-[20ch] text-[28px] font-semibold sm:text-[36px]">
        {detail.title}
      </h2>
      <p className="mt-4 max-w-[56ch] text-[16px] leading-relaxed text-muted sm:text-[17px]">
        {detail.intro}
      </p>

      <ol className="mt-10 space-y-px bg-line">
        {detail.steps.map((item) => (
          <li key={item.step} className="bg-background p-5 sm:p-6">
            <div className="flex gap-4">
              <span className="w-7 shrink-0 pt-[3px] text-[13px] font-semibold tabular-nums text-accent">
                {item.step}
              </span>
              <div className="grid flex-1 gap-4 sm:grid-cols-2 sm:gap-8">
                <div>
                  <h3 className="text-[16px] font-medium">{item.title}</h3>
                  <p className="mt-2 text-[15px] text-muted">
                    <span className="font-medium text-ink">Εσύ: </span>
                    {item.you}
                  </p>
                </div>
                <p className="text-[15px] text-muted sm:pt-7">
                  <span className="font-medium text-ink">Εμείς: </span>
                  {item.us}
                </p>
              </div>
            </div>
          </li>
        ))}
      </ol>

      <h3 className="mt-12 text-[12px] font-semibold uppercase tracking-[0.16em] text-muted">
        Τι παίρνεις κάθε μήνα
      </h3>
      <dl className="mt-5 grid gap-x-10 gap-y-5 sm:grid-cols-2 lg:grid-cols-3">
        {detail.deliverables.map((item) => (
          <div key={item.title} className="border-t border-line pt-3">
            <dt className="text-[15px] font-medium">{item.title}</dt>
            <dd className="mt-1 text-[15px] text-muted">{item.description}</dd>
          </div>
        ))}
      </dl>

      <p className="mt-8 border-l-2 border-accent pl-4 text-[15px] text-muted">
        {detail.timeCost}
      </p>
    </article>
  );
}

export function ProcessPage() {
  return (
    <div className="mx-auto max-w-[1180px] px-5 py-16 sm:px-8 sm:py-24">
      <Link to="/" className="text-[14px] text-muted transition-colors hover:text-ink">
        ← Πίσω στη σελίδα
      </Link>

      <h1 className="mt-8 max-w-[18ch] text-[36px] font-semibold sm:text-[52px]">
        {processIntro.headline}
      </h1>
      <p className="mt-5 max-w-[56ch] text-[17px] leading-relaxed text-muted sm:text-[19px]">
        {processIntro.description}
      </p>

      <div className="mt-16 space-y-16">
        {processDetails.map((detail) => (
          <ProcessBlock key={detail.offerId} detail={detail} />
        ))}
      </div>

      <div className="mt-16 border-t border-line pt-10">
        <p className="max-w-[52ch] text-[17px] text-muted">
          Αν δεν είσαι σίγουρος ποιο από τα δύο σου ταιριάζει, γράψε μας τι
          επιχείρηση έχεις και πόσο χρόνο μπορείς να διαθέσεις.
        </p>
        <a
          href={mailto("Επικοινωνία από τη σελίδα διαδικασίας")}
          className="mt-6 inline-flex items-center justify-center bg-ink px-7 py-4 text-[15px] font-medium text-background transition-colors hover:bg-accent"
        >
          Μίλα μαζί μας
        </a>
      </div>
    </div>
  );
}
