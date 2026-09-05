export type Step = {
  step: string;
  title: string;
  description: string;
};

export type Offer = {
  id: string;
  badge: string;
  featured?: boolean;
  title: string;
  description: string;
  features: string[];
  howItWorks: Step[];
  cta: string;
};

export const hero = {
  eyebrow: "SOCIAL MEDIA MANAGEMENT",
  headline: "Τα social media της επιχείρησής σου, χωρίς να τα κυνηγάς κάθε μέρα.",
  description:
    "Αναλαμβάνουμε τη διαχείριση του περιεχομένου σου με δύο τρόπους: είτε μας στέλνεις το υλικό, είτε ερχόμαστε στον χώρο σου και το δημιουργούμε εμείς.",
  primaryCta: "Δες τα πακέτα",
  secondaryCta: "Μίλα μαζί μας",
};

export const offersIntro = {
  headline: "Διάλεξε πώς θέλεις να δουλέψουμε.",
  description:
    "Δεν χρειάζονται όλες οι επιχειρήσεις το ίδιο setup. Γι' αυτό έχουμε δύο διαφορετικούς τρόπους συνεργασίας.",
};

export const offers: Offer[] = [
  {
    id: "remote",
    badge: "REMOTE",
    title: "Μας στέλνεις το υλικό. Αναλαμβάνουμε τα υπόλοιπα.",
    description:
      "Αν μπορείς να τραβάς φωτογραφίες και βίντεο από την επιχείρησή σου, εμείς τα οργανώνουμε και τα μετατρέπουμε σε περιεχόμενο έτοιμο για δημοσίευση.",
    features: [
      "Μηνιαίο πλάνο περιεχομένου",
      "Ιδέες για φωτογραφίες και βίντεο",
      "Οδηγίες για το τι πρέπει να τραβήξεις",
      "Video editing",
      "Σχεδιασμός posts και stories",
      "Captions",
      "Προγραμματισμός δημοσιεύσεων",
      "Διαχείριση Instagram και Facebook",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Παίρνεις το πλάνο",
        description: "Σου λέμε τι υλικό χρειαζόμαστε για τον μήνα.",
      },
      {
        step: "02",
        title: "Τραβάς το υλικό",
        description: "Με το κινητό σου, μέσα στην επιχείρηση.",
      },
      {
        step: "03",
        title: "Μας το στέλνεις",
        description: "Από εκεί και πέρα το αναλαμβάνουμε εμείς.",
      },
      {
        step: "04",
        title: "Το content ανεβαίνει",
        description: "Editing, design, captions και προγραμματισμός.",
      },
    ],
    cta: "Με ενδιαφέρει το Remote",
  },
  {
    id: "production",
    badge: "CONTENT PRODUCTION",
    featured: true,
    title: "Ερχόμαστε στον χώρο σου και δημιουργούμε το περιεχόμενο.",
    description:
      "Δεν χρειάζεται να σκέφτεσαι τι να τραβήξεις ή να κυνηγάς υλικό μέσα στον μήνα. Οργανώνουμε content day στον χώρο σου και δημιουργούμε εμείς φωτογραφίες και βίντεο για τα social media.",
    features: [
      "Content strategy",
      "Μηνιαίο content plan",
      "Content day στον χώρο σου",
      "Λήψη φωτογραφιών",
      "Λήψη short-form video",
      "Reels παραγωγή και editing",
      "Σχεδιασμός posts",
      "Captions",
      "Προγραμματισμός δημοσιεύσεων",
      "Διαχείριση Instagram και Facebook",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Σχεδιάζουμε τον μήνα",
        description: "Καθορίζουμε τι περιεχόμενο χρειάζεται η επιχείρηση.",
      },
      {
        step: "02",
        title: "Ερχόμαστε στον χώρο",
        description: "Κάνουμε οργανωμένο γύρισμα φωτογραφιών και βίντεο.",
      },
      {
        step: "03",
        title: "Ετοιμάζουμε το content",
        description: "Editing, design και captions.",
      },
      {
        step: "04",
        title: "Αναλαμβάνουμε τα social",
        description: "Το περιεχόμενο προγραμματίζεται και δημοσιεύεται.",
      },
    ],
    cta: "Θέλω Content Production",
  },
];

export const comparison = {
  headline: "Ποιο πακέτο σου ταιριάζει;",
  rows: [
    { feature: "Social Media Management", remote: true, production: true },
    { feature: "Content Planning", remote: true, production: true },
    { feature: "Editing", remote: true, production: true },
    { feature: "Graphic Design", remote: true, production: true },
    { feature: "Captions", remote: true, production: true },
    { feature: "Content Shooting", remote: false, production: true },
    { feature: "Παρουσία στον χώρο σου", remote: false, production: true },
  ],
};

export const finalCta = {
  headline: "Δεν είσαι σίγουρος ποιο χρειάζεσαι;",
  description:
    "Πες μας λίγα πράγματα για την επιχείρησή σου και θα σου πούμε ποια συνεργασία έχει περισσότερο νόημα.",
  cta: "Μίλα μαζί μας",
};

export const contactEmail = "hello@hyperlaunch.gr";

export type Review = {
  name: string;
  city: string;
  rating: number;
  review: string;
};

export const reviewsHeadline = "Τι λένε όσοι δούλεψαν μαζί μας.";

export const reviews: Review[] = [
  {
    name: "Αντώνης Μπάρκας",
    city: "Βόλος",
    rating: 5,
    review:
      "Αυτό που με βοήθησε περισσότερο ήταν η οργάνωση. Ξέραμε κάθε μήνα τι πρέπει να τραβήξουμε και δεν ψάχναμε τελευταία στιγμή τι να ανεβάσουμε.",
  },
  {
    name: "Ιωάννα Κεφαλά",
    city: "Λάρισα",
    rating: 5,
    review:
      "Η συνεργασία ήταν πολύ πιο απλή απ' όσο περίμενα. Έστελνα το υλικό και μετά αναλάμβαναν editing, captions και πρόγραμμα δημοσιεύσεων.",
  },
  {
    name: "Μάριος Σταθόπουλος",
    city: "Πάτρα",
    rating: 5,
    review:
      "Μου άρεσε ότι δεν προσπαθούσαν να κάνουν το περιεχόμενο υπερβολικό. Έμεινε κοντά στο ύφος της επιχείρησης και έδειχνε πιο επαγγελματικό.",
  },
  {
    name: "Δανάη Βέργου",
    city: "Θεσσαλονίκη",
    rating: 5,
    review:
      "Κάναμε ένα οργανωμένο content day και βγάλαμε υλικό για αρκετές εβδομάδες. Για μένα αυτό ήταν το μεγαλύτερο όφελος γιατί γλίτωσα πολύ χρόνο.",
  },
  {
    name: "Πέτρος Μαυρίδης",
    city: "Αθήνα",
    rating: 5,
    review:
      "Είχαμε social media αλλά χωρίς συνέπεια. Με τη συνεργασία μπήκε ένα σταθερό πρόγραμμα και πλέον η εικόνα της επιχείρησης είναι πολύ πιο καθαρή.",
  },
];

export type ProcessDetail = {
  offerId: string;
  badge: string;
  title: string;
  intro: string;
  /** Τι κάνει ο πελάτης και τι κάνουμε εμείς, σε κάθε βήμα. */
  steps: {
    step: string;
    title: string;
    you: string;
    us: string;
  }[];
  deliverables: {
    title: string;
    description: string;
  }[];
  timeCost: string;
};

export const processIntro = {
  headline: "Πώς δουλεύουμε, βήμα βήμα.",
  description:
    "Δύο τρόποι συνεργασίας, με τα ίδια παραδοτέα στο τέλος. Αυτό που αλλάζει είναι ποιος τραβάει το υλικό και πόσο χρόνο βάζεις εσύ.",
};

export const processDetails: ProcessDetail[] = [
  {
    offerId: "remote",
    badge: "REMOTE",
    title: "Μας στέλνεις το υλικό",
    intro:
      "Ταιριάζει αν έχεις κάποιον στην ομάδα που μπορεί να τραβάει με το κινητό. Εσύ δίνεις τις λήψεις, εμείς όλα τα υπόλοιπα.",
    steps: [
      {
        step: "01",
        title: "Πλάνο μήνα",
        you: "Μας λες τι τρέχει τον επόμενο μήνα: προσφορές, νέα προϊόντα, αργίες.",
        us: "Γράφουμε το πλάνο και σου στέλνουμε λίστα με το τι πρέπει να τραβήξεις.",
      },
      {
        step: "02",
        title: "Λήψεις",
        you: "Τραβάς με το κινητό μέσα στην εβδομάδα, με βάση τη λίστα.",
        us: "Είμαστε διαθέσιμοι αν κολλήσεις σε κάτι ή θες δεύτερη γνώμη.",
      },
      {
        step: "03",
        title: "Παράδοση υλικού",
        you: "Ανεβάζεις τα αρχεία σε έναν κοινό φάκελο.",
        us: "Διαλέγουμε τι κρατάμε, κάνουμε editing και σχεδιάζουμε τα posts.",
      },
      {
        step: "04",
        title: "Έγκριση και δημοσίευση",
        you: "Βλέπεις το πακέτο του μήνα και λες αν θες αλλαγές.",
        us: "Διορθώνουμε, προγραμματίζουμε και ανεβάζουμε.",
      },
    ],
    deliverables: [
      { title: "Μηνιαίο πλάνο", description: "Τι ανεβαίνει, πότε και γιατί." },
      { title: "Λίστα λήψεων", description: "Συγκεκριμένες οδηγίες για το τι να τραβήξεις." },
      { title: "Editing", description: "Μοντάζ στα βίντεο, διόρθωση στις φωτογραφίες." },
      { title: "Posts και stories", description: "Σχεδιασμένα, έτοιμα για δημοσίευση." },
      { title: "Captions", description: "Κείμενα γραμμένα στη γλώσσα της επιχείρησης." },
      { title: "Δημοσιεύσεις", description: "Προγραμματισμός σε Instagram και Facebook." },
    ],
    timeCost: "Ο δικός σου χρόνος: περίπου 2 ώρες τον μήνα για λήψεις και μία για έγκριση.",
  },
  {
    offerId: "production",
    badge: "CONTENT PRODUCTION",
    title: "Ερχόμαστε και τραβάμε εμείς",
    intro:
      "Ταιριάζει αν δεν έχεις χρόνο ή δεν θέλεις να ασχοληθείς καθόλου με τις λήψεις. Μία μέρα στον χώρο σου καλύπτει τον μήνα.",
    steps: [
      {
        step: "01",
        title: "Πλάνο μήνα",
        you: "Μας λες τι θέλεις να προβληθεί και τι δουλεύει ήδη στο μαγαζί.",
        us: "Ετοιμάζουμε shot list: τι θα τραβήξουμε, σε ποιον χώρο, με ποια σειρά.",
      },
      {
        step: "02",
        title: "Content day",
        you: "Μας ανοίγεις τον χώρο και ετοιμάζεις ό,τι θα φωτογραφηθεί.",
        us: "Ερχόμαστε με τον εξοπλισμό και τραβάμε φωτογραφίες και βίντεο.",
      },
      {
        step: "03",
        title: "Παραγωγή",
        you: "Δεν χρειάζεται να κάνεις κάτι.",
        us: "Μοντάρουμε τα reels, επεξεργαζόμαστε τις φωτογραφίες, σχεδιάζουμε τα posts.",
      },
      {
        step: "04",
        title: "Έγκριση και δημοσίευση",
        you: "Βλέπεις το πακέτο του μήνα και λες αν θες αλλαγές.",
        us: "Διορθώνουμε, προγραμματίζουμε και ανεβάζουμε.",
      },
    ],
    deliverables: [
      { title: "Content strategy", description: "Τι λέμε, σε ποιον και κάθε πότε." },
      { title: "Content day", description: "Οργανωμένο γύρισμα στον χώρο σου." },
      { title: "Φωτογραφίες", description: "Επεξεργασμένες, έτοιμες για χρήση." },
      { title: "Reels", description: "Short-form βίντεο, γυρισμένα και μονταρισμένα." },
      { title: "Posts και captions", description: "Σχεδιασμός και κείμενα." },
      { title: "Δημοσιεύσεις", description: "Προγραμματισμός σε Instagram και Facebook." },
    ],
    timeCost: "Ο δικός σου χρόνος: μισή μέρα για το content day και μία ώρα για έγκριση.",
  },
];
