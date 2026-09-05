import { contactEmail } from "../data/content";

export function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-[1180px] flex-col gap-3 px-5 py-10 text-[14px] text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <span className="font-semibold text-ink">Hyperlaunch</span>
        <a href={`mailto:${contactEmail}`} className="transition-colors hover:text-ink">
          {contactEmail}
        </a>
      </div>
    </footer>
  );
}
