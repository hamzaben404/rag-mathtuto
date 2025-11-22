# Le Guide du Coach Bienveillant : Logique Mathématique (Partie 2)
*Basé sur le cours de Mr CHEDDADI Haitam*

---

## 1. Les Lois de Morgan (Nier des groupes)
*(Source : Section 5-2)*

### Pourquoi ça existe ? (The Hook)
C'est le code de sécurité pour ne pas se tromper quand on veut dire le contraire d'une phrase complexe.

### L'Analogie (The Analogy)
Le menu "Burger **ET** Frites".
Si je refuse ce menu ($\overline{ET}$), je ne dis pas que je ne veux ni l'un ni l'autre.
Je dis juste que la combinaison est impossible. Soit le burger manque, **OU** les frites manquent.

### Le Lien (The Bridge)
* $\overline{P \text{ et } Q} \Leftrightarrow \overline{P} \text{ ou } \overline{Q}$
* $\overline{P \text{ ou } Q} \Leftrightarrow \overline{P} \text{ et } \overline{Q}$
L'astuce : Le trait de la négation agit comme une épée. Il coupe le connecteur en deux :
* Le "$\wedge$" (et) coupé devient "$\vee$" (ou).
* Le "$\vee$" (ou) coupé devient "$\wedge$" (et).

### L'Image Mentale (The Visual)
Un miroir inversé. Tout ce qui est "Et" devient "Ou". Tout ce qui est "Vrai" devient "Faux".
Imagine que tu retournes une chaussette : l'intérieur devient l'extérieur.

---

## 2. Le Raisonnement par Contraposée
*(Source : Section 5-3)*

### Pourquoi ça existe ? (The Hook)
C'est une "porte dérobée". Quand la porte principale (prouver $P \Rightarrow Q$) est bloquée, on passe par derrière ($\overline{Q} \Rightarrow \overline{P}$) pour entrer plus facilement.

### L'Analogie (The Analogy)
L'inspecteur de police.
* Phrase directe : "Si c'est le tueur, alors il a des traces de boue." (Difficile à prouver si on ne sait pas qui est le tueur).
* Contraposée : "S'il n'a pas de trace de boue, alors ce n'est pas le tueur." (Très facile : regarde les chaussures, si elles sont propres, tu l'innocentes direct).

### Le Lien (The Bridge)
Au lieu de montrer une inégalité compliquée ($x \neq y \Rightarrow f(x) \neq f(y)$), on montre l'égalité correspondante ($f(x) = f(y) \Rightarrow x = y$). C'est souvent beaucoup plus simple de manipuler des égalités (=) que des "différent de" ($\neq$).

### L'Image Mentale (The Visual)
Un film rembobiné.
Si le film va du début ($P$) à la fin ($Q$), le rembobinage va de la fin effacée ($\overline{Q}$) au début effacé ($\overline{P}$). C'est la même bande !

---

## 3. Le Raisonnement par l'Absurde
*(Source : Section 5-4)*

### Pourquoi ça existe ? (The Hook)
C'est l'arme des têtu(e)s. Pour prouver que tu as raison, tu fais semblant d'être d'accord avec ton adversaire jusqu'à ce qu'il dise une bêtise énorme.

### L'Analogie (The Analogy)
Imagine que tu veux prouver qu'il ne pleut pas.
Tu dis : "OK, supposons qu'il pleut."
Tu regardes dehors : "Si il pleut, les gens devraient avoir des parapluies. Or, personne n'a de parapluie et tout le monde bronze en maillot de bain."
Conclusion : Ta supposition de départ ("il pleut") était fausse. Donc il ne pleut pas.

### Le Lien (The Bridge)
Pour montrer que $P$ est vraie :
1.  On suppose $\overline{P}$ (le contraire).
2.  On calcule...
3.  On tombe sur une horreur (comme $0=1$ ou $\sqrt{2}$ est rationnel).
4.  On dit "Absurde !". Donc notre supposition était fausse. Donc $P$ est vraie.

---

## 4. Le Raisonnement par Récurrence
*(Source : Section 5-6)*

### Pourquoi ça existe ? (The Hook)
C'est la seule façon de prouver qu'une règle marche pour l'infini, sans avoir à tester l'infini.

### L'Analogie (The Analogy)
La chute de **Dominos**.
Pour que tous les dominos tombent, tu dois vérifier deux choses :
1.  Le premier domino tombe (Initialisation).
2.  Chaque domino qui tombe entraîne le suivant (Hérédité).

### Le Lien (The Bridge)
Pour prouver une propriété $P(n)$ pour tout $n$ :
1.  **Initialisation :** Vérifie $P(0)$ ou $P(1)$. (On pousse le premier).
2.  **Hérédité :** Suppose que $P(n)$ est vraie (le domino $n$ tombe) et montre que $P(n+1)$ est vraie (le domino $n+1$ tombe aussi).

### L'Image Mentale (The Visual)
Une échelle infinie.
Si tu sais monter sur la première marche, et que tu sais passer de n'importe quelle marche à la suivante... alors le ciel est la limite !