import { Hero } from "../components/Hero";
import { Offers } from "../components/Offers";
import { Comparison } from "../components/Comparison";
import { Reviews } from "../components/Reviews";
import { FinalCta } from "../components/FinalCta";

export function Home() {
  return (
    <>
      <Hero />
      <Offers />
      <Comparison />
      <Reviews />
      <FinalCta />
    </>
  );
}
