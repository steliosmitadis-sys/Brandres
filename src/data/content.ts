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
