import { contactEmail } from "../data/content";

export function Navigation() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1180px] items-center justify-between px-5 sm:px-8">
        <a href={import.meta.env.BASE_URL} className="text-[17px] font-semibold tracking-tight">
          Hyperlaunch
        </a>

        <nav className="flex items-center gap-6">
          <a
            href={`${import.meta.env.BASE_URL}#offers`}
            className="hidden text-[14px] text-muted transition-colors hover:text-ink sm:block"
          >
            Πακέτα
          </a>
          <a
            href={`${import.meta.env.BASE_URL}#comparison`}
            className="hidden text-[14px] text-muted transition-colors hover:text-ink sm:block"
          >
            Σύγκριση
          </a>
          <a
            href={`mailto:${contactEmail}`}
            className="border border-ink px-4 py-2 text-[14px] font-medium transition-colors hover:bg-ink hover:text-background"
          >
            Επικοινωνία
          </a>
        </nav>
      </div>
    </header>
  );
}
