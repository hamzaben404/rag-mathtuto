![](https://cdn-mineru.openxlab.org.cn/result/2025-11-10/8b5b8822-8ec7-40b0-b020-7f5258f0a2be/a1f37cbdd17151b74b9b8ae2a1ee819dc5db194a4605feaeebd83fd53296afc7.jpg)

# AlloSchool

Mathématiques : 1Bac SM

Séance 1-2-1 : Notion de logique - Partie 2 (Cours)

Professeur : Mr CHEDDADI Haitam

Sommaire

# V- Lois logiques et raisonnements

5-1/ Loi logique ou tautologie  
5-2/ Lois de Morgan  
5-3/ Raisonnement par contraposée  
5-4/ Raisonnement par l'absurde  
5-5/ Raisonnement par disjonction des cas  
5-6/ Raisonnement par récurrence

# V- Lois logiques et raisonnements

# 5-1/ Loi logique ou tautologie

# Définition

Soit  $Q_{1}, Q_{2}, \ldots, Q_{n}$  des propositions.

On appelle loi logique ou tautologie toute proposition  $P$  réalisante de l'assemblage par des connecteurs logiques de propositions prises parmi  $Q_{1}, Q_{2}, \ldots, Q_{n}$  qui est vraie qu'elle que soit la valeur de vérité des propositions en jeu.

# Applications

Soit  $P$  et  $Q$  deux propositions.

1. Montré que les propositions suivantes sont des lois logiques :

$$
\begin{array}{l} P \Rightarrow (Q \Rightarrow P) \\ P \Rightarrow (\overline {{P}} \Rightarrow Q) \\ \left(\overline {{Q}} o u P\right) o u \left(Q o u \overline {{P}}\right) \\ (P \Leftrightarrow Q) \Leftrightarrow \left[ (P e t Q) o u (\bar {P} e t \bar {Q}) \right] \\ \end{array}
$$

# 5-2/ Lois de Morgan

# Proposition

Soit  $P$  et  $Q$  deux propositions.

Les deux propositions suivantes sont des lois logiques :

$$
\begin{array}{c} \overline {{(P e t Q)}} \Leftrightarrow (\overline {{P}} o u \overline {{Q}}) \\ \overline {{(P o u Q)}} \Leftrightarrow (\overline {{P}} e t \overline {{Q}}) \end{array}
$$

# Applications

Soit  $P$  et  $Q$  deux propositions.

1. Déterminer la négation des propositions suivantes :

$$
\begin{array}{l} P: \ll (\exists x \in \mathbb {R}) 0 \leq x <   1 \gg \\ Q: \ll (\forall x \in \mathbb {R}) (x ^ {2} = 1 \Rightarrow x = 1) \gg \\ R: \ll (\forall a \in \mathbb {R}) (| a + 1 | \leq 2 \Rightarrow a \geq - 3) \gg \\ S: \ll (\forall x \in \mathbb {R}) (\forall y \in \mathbb {R} ^ {+}) (x ^ {2} \leq y ^ {2} \Leftrightarrow - y \leq x \leq y) \gg \\ \end{array}
$$

# 5-3/ Raisonnement par contraposée

# Proposition

Soit  $P$  et  $Q$  deux propositions.

L'implication  $\overline{Q} \Rightarrow \overline{P}$  s'appeille la contraposée (ou l'implication contraposée) de l'implication  $P \Rightarrow Q$ .

La contraposee d'une implication est equivalente à celle-ci:

$$
(P \Rightarrow Q) \Leftrightarrow (\overline {{Q}} \Rightarrow \overline {{P}})
$$

# Remarques

Il faut bien désigner entre la négation, la contraposée et la réciproque :

- La négation de  $P \Rightarrow Q$  est  $(P \text{ et } \overline{Q})$ .  
- La réciproque de  $P \Rightarrow Q$  est  $Q \Rightarrow P$ .  
- La contraposée de  $P \Rightarrow Q$  est  $\overline{Q} \Rightarrow \overline{P}$ .

Le recours au raisonnement par contraposée n'est évidemment pertinent que si cette contraposée est plus facile à couver que l'implication directe.

# Applications

1. En utilisant le raisonnement par contraposée, montré les implications suivantes :

1  $(\forall x\in [-1; + \infty [)$  ）  $\left(x\neq 0\Rightarrow \sqrt{1 + x}\neq 1 + \frac{x}{2}\right)$

$\boxed{2} (\forall x \in \mathbb{R}) \left(x^{2} \neq 3 \Rightarrow \frac{2}{\sqrt{1 + x^{2}}} \neq 1\right)$

$\left(\forall (x; y) \in \mathbb{R}^{2}\right)$ $(4y \neq -3x \Rightarrow x - y \neq 7(x + y))$

$\left(\forall (x; y) \in \mathbb{R}^{2}\right)\left((xy - 1)(x - y) \neq 0 \Rightarrow x(y^{2} + y + 1) \neq y(x^{2} + x + 1)\right)$

$\left(\forall (x; y) \in ([1; +\infty[)^2\right)$ $(x \neq y \Rightarrow x^2 - 2x \neq y^2 - 2y)$

$\boxed{6} (\forall x \in \mathbb{R}) (x \notin [-1;4] \Rightarrow x^2 - 3x - 4 > 0)$

$\boxed{7} (\forall x \in \mathbb{R}^{+}) (x \neq 0 \Rightarrow \frac{1}{1 + \sqrt{x}} \neq 1 - \sqrt{x})$

8  $(\forall (x;y)\in \mathbb{R}^2)(x^2 +y^2\leq 1\Rightarrow |x + y|\leq 2)$

$\left(\forall (x; y) \in \mathbb{R}^{2}\right)\left(|2x^{2} + 5xy + 3y^{2}| \leq 3 \Rightarrow \left(|x + y| \leq 3 \text{ ou } |2x + 3y| \leq \sqrt{3}\right)\right)$

$\boxed{10}\left(\forall (x;y)\in \mathbb{R}^2\right)\left(x^2 +xy + y^2\leq 3\Rightarrow \left(|x + 2y|\leq 2\sqrt{3} et|x|\leq 2\right)\right)$

# 5-4/ Raisonnement par l'absurde

# Proposition

Soit  $P$  et  $Q$  deux propositions.

La proposition suivante est une loi logique :

$$
\left[ \left(\bar {P} \Rightarrow Q\right) e t \left(\bar {P} \Rightarrow \bar {Q}\right) \right] \Rightarrow P
$$

# Applications

Soit  $a, b$  et  $c$  des réels positifs tels que  $ab < c$ .

1. Montrer que:  $a < \sqrt{c}$  ou  $b < \sqrt{c}$

Soit  $f$  une fonction numérique définie sur  $\mathbb{R}$  telle que pour tout

$$
(x; y) \in (\mathbb {R} ^ {*}) ^ {2}: f (x y) = f (x) f (y)
$$

On suppose que  $f(1) \neq 0$ .

2. Montrer que:  $(\forall x \in \mathbb{R}^{*}) f(x) \neq 0$  
3. Montré par l'absurde que:  $(\forall n \in \mathbb{N}) \sqrt{4n + 2} \notin \mathbb{N}$

# 5-5/ Raisonnement par disjonction des cas

# Proposition

Soit  $P$  et  $Q$  deux propositions.

La proposition suivante est une loi logique :

$$
[ (P \Rightarrow R) e t (Q \Rightarrow R) ] \Leftrightarrow [ ((P o u Q) \Rightarrow R) ]
$$

# Applications

1. Résoudre dans  $\mathbb{R}$  les inéquations suivantes:

$$
\begin{array}{l} (I _ {1}) \left| x ^ {2} - 4 \right| - x ^ {2} > 0 \\ \left(I _ {2}\right) \left| 2 x - 1 \right| + \left| 2 x + 1 \right| + | x | \geq 4 \\ \left(I _ {3}\right) \sqrt {3 - x} + x <   0 \\ \end{array}
$$

2. Montrer que le produit de trois entiers relatifs consécutifs est divisible par 6.  
3. Montrer que pour tout  $x \in \mathbb{R}$ :

$$
\begin{array}{l} \left. a\right) x + \sqrt {x ^ {2} + 1} > 0 \\ b) | x | + | x + 1 | + | x - 1 | \neq 0 \\ c) | x - 1 | \leq x ^ {2} - 2 x + 2 \\ \end{array}
$$

Soit  $a, b$  et  $c$  trois réels tels que  $c$  est positif.

4. En utilisant un raisonnement par disjonction des cas, montré les deux implications suivantes :

$$
\left(| a | \leq c e t | b | \leq c\right) \Rightarrow | a + b | + | a - b | \leq 2 c
$$

$$
\left| a + b \right| + \left| a - 2 b \right| \leq 3 c \Rightarrow \left(\left| a \right| \leq 2 c e t | b | \leq c\right)
$$

Soit  $n$  un entier naturel.

5. Démontré que si  $n$  est impair, alors il s'écrit sous la forme  $n = 4k + 1$  ou  $n = Ak + 3$  avec  $k \in \mathbb{N}$ .  
6. Déduire que si l'entier  $n^2 - 1$  n'est pas divisible par 8, alors l'entier  $n$  est pair.

# 5-6/ Raisonnement par récurrence

# Proposition

Soit  $P(n)$  une fonction propositionnelle qui dépend d'un entier naturel  $n$  et  $n_0 \in \mathbb{N}$ .

Si la proposition  $P(n_0)$  est vraie et si l'implication «  $P(n) \Rightarrow P\{n + 1\}$  » est vraie pour tout  $n \geq n_0$ , alors, la proposition  $P(n)$  est vraie, pour tout entier  $n \geq n_0$ .

# Applications

1. Montré par récurrence que pour tout  $n \in \mathbb{N}^*$ :

$$
\begin{array}{l} 1 + 2 + \dots + n = \frac {n (n + 1)}{2} \\ 1 ^ {3} + 2 ^ {3} + \dots + n ^ {3} = \frac {n ^ {2} (n + 1) ^ {2}}{4} \\ 1 \times 2 + 2 \times 3 + \dots + n (n + 1) = \frac {n (n + 1) (n + 2)}{3} \\ \end{array}
$$

2. Montrer par récurrence que pour tout  $n \in \mathbb{N}^*$ :  $5^{2n+1} + 2^{n+4} + 2^{n+1}$  est divisible par 23.

Soit  $a$  et  $b$  deux réels distincts et strictement positifs.

3. Montrer par récurrence que:  $(\forall n \in \mathbb{N}) \left(\frac{a + b}{2}\right)^n \leq \frac{a^n + b^n}{2}$