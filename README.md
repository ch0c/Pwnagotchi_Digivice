# Digivice – A Digimon Evolution Plugin for Pwnagotchi  

![Alt text](preview.png)

Turn your Pwnagotchi into a digital monster with **Digivice Plugin**, a plugin inspired by classic Digivices! Just like in the old-school Digimon toys, your Pwnagotchi will gain experience (EXP), grow older, and evolve into different forms based on its activity.  

---

## 🚀 Features  

- **EXP System** – Earn EXP from handshakes, associations, and deauthentication attacks.  
- **Evolution Paths** – Start with **Agumon** or **Gabumon**, then evolve into:  
  - Greymon, MetalGreymon  
  - Garurumon, Metal Garurumon  
  - Numemon, Monzaemon  
  - Kabuterimon, Skull Greymon  
- **Dynamic Faces** – Your Pwnagotchi's face updates automatically as it evolves.  
- **Live Stats** – Displays your Digimon’s **form, age, EXP bar, and handshake count** in the UI.  
- **Auto-Saving & Config Updates** – Tracks progress and updates `config.toml`.  
- **Auto-Restart on Evolution** – Ensures smooth transitions when evolving.  
- **Evolution Reset** – Every **5 days**, your Digimon resets to an egg for a fresh start.  

---

## 🔥 Evolution Rules  

### 📅 At 2 Days Old  
| Starting Form | Evolution (EXP ≥ 500) | Evolution (EXP ≤ 499) |
|--------------|--------------------|--------------------|
| Agumon      | Greymon            | Numemon            |
| Gabumon     | Kabuterimon        | Garurumon          |

### 🏆 At 1000 EXP  
| Current Form  | Evolution |
|--------------|-----------|
| Greymon     | Metal Greymon |
| Numemon     | Monzaemon |
| Kabuterimon | Skull Greymon |
| Garurumon   | Metal Garurumon |

---

### Config Options.

```
main.plugins.digivice.enabled = true
main.plugins.digivice.starter = "random"  # Choose 'agumon', 'gabumon', or 'random'
main.plugins.digivice.xpbar = true
main.plugins.digivice.xpbar_position = "53,62"
```

### Tweak-View Options. 

```
    "VSS.name.xy": "400,400",
    "VSS.face.xy": "0,26",
    "VSS.status.font": "Deja 9"
```




❤️ Credits and Thanks.

Akiyoshi Hongo, Bandai, Pwnagotchi devs, airshuffler for the sprites and everyone else who made their plugins public. 
