# Sobaken-ID
The goal of the project is to try to create a computer vision service for searching for lost animals on the Internet. 

## Problem
- In simple human terms: “searching for animals by distinctive features: size, color, coat pattern, cropped ear, broken tail, collar, and so on. Adjusted for weather/lighting/animal condition/dirt on the coat/extraneous objects in the photo.”
- From a technical point of view, since this is a search, the word2vec approach (or more precisely, img2vec) may be suitable. That is, for example, we build a database of vectors of available animals (animal ID -> vector from the last layer of the model + additional features) and for each new animal we generate the same vector from the same model and search the database.

<details>
  <summary>Features</summary>
1. False negative results are critical. It is bad if the target animal disappears from the sample. On the other hand, if we produce more false positives, the person can find the animal themselves (in reasonable quantities and sorted by decreasing similarity).
2. In the early stages, it is more important to focus on dogs — they are much more difficult to rehome, treat, overstay, and so on.
</details>

# Initial results
The screenshots in the first column show the photo request, while the remaining five columns show what the model selected as the most suitable from approximately 500 photos of animals that the model did not see during training (1,000 photos - train, 500 - test). The photos are automatically segmented (the entire background is cropped).

1.
<img width="1594" alt="Screenshot 2024-10-24 at 11 54 51" src="https://github.com/user-attachments/assets/9b33d7c0-047b-4e57-b3ac-160e4ed9d80c">
2.  
<img width="1674" alt="Screenshot 2024-10-24 at 11 56 07" src="https://github.com/user-attachments/assets/3bc6e2c4-3681-49fd-9fe0-4f12a12ea21d">
3.  
<img width="1715" alt="Screenshot 2024-10-24 at 11 57 32" src="https://github.com/user-attachments/assets/222d39be-dd5c-4e4e-9889-f0f0238a868f">


And that's considering a very small dataset of 1,000 photos; we are currently preparing a dataset of 60,000 photos.

### How it works
- How it works internally - an example of a temperature map shows “where the model is looking” when generating similarity vectors:
- <img width="1719" alt="heat" src="https://github.com/user-attachments/assets/33f55772-c99d-4837-9555-d8035cda01e2">


### How to run locally
- Install Poetry
- `poetry shell` from the project root
- Download the data, configure the paths to it in the appropriate file, and run

# Contacts
My Telegram [@kella18](https://t.me/kella18)
