import { Navigation } from "./components/Navigation";
import { Hero } from "./components/Hero";
import { Offers } from "./components/Offers";
import { Reviews } from "./components/Reviews";
import { Comparison } from "./components/Comparison";
import { FinalCta } from "./components/FinalCta";
import { Footer } from "./components/Footer";

function App() {
  return (
    <>
      <Navigation />
      <main>
        <Hero />
        <Offers />
        <Comparison />
        <Reviews />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}

export default App;
