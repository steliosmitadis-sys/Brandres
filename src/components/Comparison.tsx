import { comparison } from "../data/content";

function Mark({ on }: { on: boolean }) {
  return on ? (
    <span className="text-accent" aria-label="Περιλαμβάνεται">
      <svg className="mx-auto h-4 w-4" viewBox="0 0 16 16" fill="none" aria-hidden>
        <path
          d="M3 8.5 6.5 12 13 4.5"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="square"
        />
      </svg>
    </span>
  ) : (
    <span className="text-muted/60" aria-label="Δεν περιλαμβάνεται">
      <svg className="mx-auto h-4 w-4" viewBox="0 0 16 16" fill="none" aria-hidden>
        <path d="M4 8h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="square" />
      </svg>
    </span>
  );
}

export function Comparison() {
  return (
    <section id="comparison" className="border-b border-line">
      <div className="mx-auto max-w-[1180px] px-5 py-20 sm:px-8 sm:py-24">
        <h2 className="text-[32px] font-semibold sm:text-[44px]">
          {comparison.headline}
        </h2>

        <div className="mt-10 overflow-x-auto">
          <table className="w-full min-w-[520px] border-collapse text-left">
            <thead>
              <tr className="border-b border-ink">
                <th className="py-4 pr-4 text-[13px] font-semibold uppercase tracking-[0.14em] text-muted">
                  Τι περιλαμβάνει
                </th>
                <th className="w-32 py-4 text-center text-[13px] font-semibold uppercase tracking-[0.14em] text-muted">
                  Remote
                </th>
                <th className="w-40 py-4 text-center text-[13px] font-semibold uppercase tracking-[0.14em]">
                  Production
                </th>
              </tr>
            </thead>
            <tbody>
              {comparison.rows.map((row) => (
                <tr key={row.feature} className="border-b border-line">
                  <td className="py-4 pr-4 text-[15px]">{row.feature}</td>
                  <td className="py-4 text-center">
                    <Mark on={row.remote} />
                  </td>
                  <td className="py-4 text-center">
                    <Mark on={row.production} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
