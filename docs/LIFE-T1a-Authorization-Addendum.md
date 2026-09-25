# LIFE — T1a Build Spec Addendum: "enostavna avtorizacija"

## Zahteva

Dodajanje vira (trenutno Gmail, kasneje Outlook/iCloud v T2) mora biti za uporabnika en klik na gumb **"Poveži [ponudnik]"** in nič več — brez dodatnih obrazcev in brez ročnega vnosa nastavitev.

Pred klikom se prikaže en kratek stavek, kaj se bo bralo in da je dostop kadarkoli preklicljiv.

Ko se kasneje doda Outlook ali iCloud, se uporabi isti vzorec gumba/toka kot za Gmail — brez redizajna avtorizacijskega toka za vsakega novega ponudnika.

## Acceptance kriterij — MVP checklist, postavka 12

**Given** nov uporabnik na zaslonu za povezavo,  
**when** klikne **"Poveži Google račun"** in odobri dostop,  
**then** je od klika do prikaza prvega Today zaslona z realnimi podatki **manj kot 2 minuti**, brez dodatnih obrazcev.

Če OAuth tok katerega koli ponudnika to presega, je to napaka, ki **blokira prehod na testiranje s piloti** — ni kozmetična pripomba.

## Implementation requirement

The provider connection UI must be provider-driven rather than hard-coded per provider: each provider is represented by the same connection-card pattern (id, display label, one-click action, short read-access explanation). Adding Outlook/iCloud in T2 should require adding a provider definition and its backend OAuth implementation, not redesigning the connection screen.

## Current T1a status

Google is the first provider. The current frontend uses a provider registry and a single-click **"Connect Google account"** action; no additional LIFE form is shown before the Google OAuth consent screen.
