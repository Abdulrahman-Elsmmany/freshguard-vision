# The FreshGuard Story

> A living memoir of how this project actually unfolded — the brief, the failure on real photos, the diagnosis, the research, and the rebuild. I keep it open as I work and update it after every meaningful step, so by the time another public release ships, the narrative is already complete.
>
> _Last updated: 2026-05-13_

---

## Act 1 — The brief

I wanted a portfolio piece that did one thing well: look at a photo of fruit or vegetables and tell you whether it was fresh or rotten. Not a toy classifier on a clean studio dataset — a single deployable thing with a Streamlit demo, honest metrics, and a story I could point a recruiter at.

I picked **24 classes** on purpose. Twelve produce types crossed with `{fresh, rotten}`. The joint label space matters: if the type model and the freshness model live in two different heads, sooner or later they disagree about what they're looking at, and the cascade-error class of bug eats your weekend. One label, one truth.

The architecture I shipped first was a **two-stage with a fallback**: a YOLO26s detector emitting all 24 labels in a single forward pass, and an EfficientNetV2-S classifier behind it for cases where the detector found no boxes. Trained on Kaggle's `ulnnproject/food-freshness-dataset` (~70k images), with a real engineering pass under the hood — corrupt-file pruning, pHash deduplication, cluster-disjoint 70/15/15 splits stratified by `produce_type × freshness`, weighted sampling and class-weighted CE for the 41:1 imbalance, RandAugment + mixup, EMA, macro F1 as the model-selection metric.

The numbers came back honest: classifier macro F1 **0.81**, end-to-end joint accuracy **0.83**, classifier top-1 **0.84**, abstention rate **4.1%** under a 0.40 confidence threshold. I shipped v0.2.0, wrote the README, drew the Mermaid architecture diagram, called it a portfolio.

Then I tried it on five photos I took with my phone.

---

## Act 2 — The reality check

Five apples. Red apples on a wood cutting board. Apples on burlap. A cross-section. A wrinkled apple. A spotted apple.

The model got **zero of five right.** Two of them it got confidently wrong — the apples on warm wood came back as `potato_fresh` with the kind of confidence the model usually reserves for the studio shots it was trained on. The wrinkled one became `carrot_rotten`. The spotted one came in at 0.39 — just under the abstain threshold, but pointing at the wrong class anyway.

I sat with that for an evening. The metrics weren't lying — they were just measuring the wrong thing. The Kaggle source dataset is overwhelmingly cropped single fruits on white or near-white backgrounds. I had built a model that knew, with high accuracy, what a fruit on a white tablecloth was. The classifier wasn't looking at the apple. It was looking at the wood.

This is the moment a portfolio project either ends or gets honest. You either ship the white-background metrics and hope nobody tests it, or you accept that what you have is a 0.83 score on a benchmark and a 0/5 score on the real world, and you treat the gap as the actual problem.

---

## Act 3 — Phase A: the inference-side fixes (already shipped)

Before tearing the model down, I tried to recover what I could from the trained weights with inference-time changes only. The full pass landed in commit `a39d1bf`:

- **Preprocessing alignment.** The Streamlit pipeline was using a slightly different normalization than training. Tiny but real.
- **Hflip TTA, always on.** Average the softmax over the original and the horizontal flip.
- **Entropy gate.** If the predictive distribution is too flat (entropy > 2.5 nats), abstain — flat distributions on real photos are the model telling me it doesn't know.
- **Full-image vs per-crop ensemble.** Run the classifier on the detector's crop _and_ on the full image. If they disagree on type, that's a genuine OOD signal, abstain.
- **Top-1 + margin abstain stack.** Below 0.40 top-1, or below 0.15 margin to the runner-up, abstain.
- **UI abstain reasons.** When the system refuses, the card says _why_ — entropy too high, margin too tight, ensemble disagreement. Honest refusal beats confident hallucination.

Same five apples after Phase A: **3/5 correct + 2/5 honest abstain.** The cross-section abstained (it's genuinely OOD — the model never saw a sliced apple in training), and one of the spotted shots abstained. No more confident wrong answers.

That was a real win. But it also closed the door on inference-side gains. The features themselves were biased. The model had learned to use background tone as a feature, and no threshold tuning fixes a wrong feature. To go further I needed different features.

---

## Act 4 — The diagnosis and the research

The right question wasn't "what threshold do I tune?" It was "what backbone produces features that don't latch onto warm-toned backgrounds?"

I spent two passes of deep web research in May 2026 on this. I considered keeping EfficientNetV2 and just retraining on a more diverse dataset — but the failure mode wasn't dataset-only. ImageNet-supervised features bias toward texture and dominant color, and the apple-on-wood failure is exactly the kind of thing supervised features over-fit to. I considered distillation from a larger CLIP model — interesting, but it adds engineering surface without a clear portfolio story. I rejected it.

The choice that came out of the audit was **DINOv3 ViT-S/16** — Meta's August 2025 release, 21M parameters, self-supervised on 1.7B images. The whole point of self-supervised pretraining is that the model doesn't get to use class labels as a shortcut. Its features are the ones that survive across views, augmentations, and crops of the same content. They don't reward latching onto background tone, because background tone changes between two crops of the same image.

For the detector, I went with **YOLO26n** (Ultralytics, January 2026). I had been on YOLO26s, but the new tiny variant ships ProgLoss + STAL specifically for small-object accuracy, runs end-to-end NMS-free inference (which simplifies the Streamlit deploy — one less knob), and is roughly 31% faster on CPU than YOLO11n. Picking the current generation matters here; portfolio projects show the kind of judgment you make when picking foundations.

I also flipped the detector's job. In v1 the detector emitted all 24 labels and the classifier was a fallback. In v2 the detector becomes **one class only — `produce`.** It draws boxes. The classifier is the single authority on type and freshness, and it sees a clean crop. This means the detector training stops fighting the 41:1 imbalance and the classifier stops fighting whatever the detector got wrong. Cleaner contract, simpler failure modes.

---

## Act 5 — The rebuild (in progress)

The plan, executable across five Kaggle notebooks `kaggle_0[1-5]_*_v2.ipynb`:

The dataset stack expands. The original Kaggle freshness data stays — that's where the freshness labels live. To it I'm adding the **KTH GroceryStoreDataset** (5,125 phone-shot photos with official train/val/test splits — exactly the failure-mode I hit), and a filtered **Open Images V7** fruit/vegetable subset for training the 1-class detector on real-world boxes. Cross-source pHash deduplication runs before splitting, otherwise reported metrics leak.

The augmentation pipeline gets the one move that targets the apple-on-wood failure directly: **Albumentations CopyPaste**, pasting fruit foregrounds onto Places365 backgrounds (kitchens, markets, tables, counters). If the training data has apples on wood, the inference time isn't the first time the model sees apples on wood. MixUp + CutMix stay (with same-category mixing for fine-grained), RandAugment level 9, color jitter 0.5 because real apple skins vary wildly, and class-balanced focal loss for the imbalance.

The classifier wraps DINOv3 ViT-S/16 with **LoRA r=16** on the last two transformer blocks plus a small MLP head (384 → 512 → 24). This keeps the total parameter footprint tiny — most of the backbone stays frozen — and means the LoRA adapter + head fits comfortably in the deploy budget. AdamW with separate learning rates (3e-4 for the head, 3e-5 for LoRA), cosine schedule, 10–15 epochs.

The honest portfolio number lands on the **GroceryStoreDataset official test split** — a benchmark I never trained on, with published WACV 2019 baselines I can compare to. That's the number I'll quote on LinkedIn. The five-apple smoke set continues to live alongside as the qualitative gut-check.

Acceptance for the rebuild is set up front: classifier top-1 ≥ 0.88 with abstain rate < 5%, macro F1 ≥ 0.82, detector mAP50 ≥ 0.85 in-distribution and ≥ 0.70 on a sampled GroceryStore shelf scene, and on the five real apples I want **at least 4/5** with the cross-section allowed to abstain. Stretch is 5/5.

The full execution plan lives at `C:\Users\abdoe\.claude\plans\i-have-six-images-wise-volcano.md`.

On 2026-05-06 I wired the local app side of that contract into the repo. The Streamlit runtime now expects a YOLO26n `produce` localizer and a DINOv3-S/16 classifier, and the pipeline no longer treats detector classes as type or freshness evidence. Each detected crop goes through the classifier, while the full-image classifier stays as a sanity check; if both are confident and disagree on produce type, the app abstains. The metrics have not changed yet, because the Kaggle v2 notebooks still have to produce the new detector, classifier, and evaluation report before the README numbers can move.

Later that same day I added the v2 Kaggle execution rails and then tightened them around official sources. Notebook 0 fetches KTH GroceryStoreDataset from its official GitHub repo and a filtered Open Images V7 produce subset through FiftyOne. Notebook 1 builds the Food Freshness canonical split and keeps KTH as separate external/type-only evidence plus low-weight `fresh_assumed` auxiliary data. Notebook 2 prepares the one-class detector data from Food Freshness, KTH, and Open Images boxes. Notebook 3 trains YOLO26n, notebook 4 trains DINOv3-S/16 with LoRA merged into the runtime checkpoint, and notebook 5 writes the v2 evaluation report. The old v1 notebooks stay in place as the receipt for the shipped baseline.

On 2026-05-10 the long Kaggle detector run timed out after reaching epoch 28/60, but it had already produced a usable `best.pt`, so I packaged that checkpoint as the v2 detector artifact instead of spending more GPU time chasing the nominal 60-epoch target. The final v2 evaluation report landed the Food Freshness 24-class classifier at **0.9478 macro F1** and **0.9490 top-1 accuracy**, the KTH GroceryStoreDataset external type-only benchmark at **0.8995 accuracy** across 955 official test images, and the one-class detector at **0.8763 mAP50 / 0.8249 mAP50-95**. The five-apple smoke images were not attached to that Kaggle run, so the external benchmark is now real but the original phone-photo gut-check still needs one more local pass before the story can close.

---

## Act 6 — Why this story matters

Most freshness classifier repos stop at Act 1 — clean dataset, good macro F1, README, done. The numbers are real, the project is real, but the model has never met the open-world images people actually upload and nobody has been honest about it.

What I want this repo to show is the loop you actually run as an ML engineer: **ship → test on real data → admit the gap honestly → diagnose at the feature level → research alternatives with current sources → rebuild from foundations up → measure on an external benchmark.** Every act in this story is a decision a real project would ask you to make, and the rebuild is the one that proves you'd make them. The first version was good enough to ship. The reason there's a second version is the part that's hard to fake.

When the v2 numbers land, the README headline shouldn't read like a hero shot. It should read like the receipt for a journey: 0/5 → 3/5 honest → 4/5 with an external benchmark to prove it generalizes.

---

## Act 7 — The open-world correction

On 2026-05-12 I caught a wording problem and a model-system problem at the same time. I had been using "phone photos" as shorthand because the original smoke set came from my own camera and KTH is a grocery-photo benchmark. That shorthand was too narrow. The app is a public GitHub project, and the real input space is broader: web images, stock-like images, grouped produce, screenshots, cluttered scenes, and images that contain no produce at all.

Two new local checks made the gap concrete. A car image from `C:\Users\abdoe\Desktop\test_img\DSC_5903.webp` produced one near-full-frame YOLO `produce` box at 0.8928 confidence, then the closed-set DINOv3 head called it `cucumber_fresh` at 0.4467. A grouped apple image from the same folder showed the opposite side of the detector problem: at the old 0.40 detector threshold it kept one real apple box and one almost-whole-image box, while the other apples lived just below the threshold. Lowering the detector threshold to 0.20 exposed those item boxes, but also made it clear that runtime post-processing had to drop scene-level boxes instead of rendering them as observations.

I patched the local runtime as a v2.1 quality step, not a demo trick. The app now rejects no-box uploads instead of asking the 24-class classifier to guess, suppresses near-full-image boxes when smaller item-level boxes exist, rejects weak single full-frame commits as non-produce, and keeps type information when the classifier is split only on fresh versus rotten. That did not replace the proper training fix, so I moved the model-side v2.1 work onto existing validated data instead of a hand-built private set: notebook 00 now materializes Open Images V7 positive produce boxes and negative/background images, notebook 02 turns the negatives into empty YOLO labels, notebook 03 emits `yolo26n_produce_v2_1.pt`, and notebook 05 reports open-world false-accept and retention metrics from that source.

On 2026-05-13 the v2.1 evaluation run finished and replaced the public report. The classifier numbers stayed where they should: **0.9478 macro F1** and **0.9490 top-1 accuracy** on the Food Freshness 24-class test split, with **0.8995** KTH type-only external accuracy across 955 official test images. The new detector landed at **0.8693 mAP50 / 0.8190 mAP50-95** and, more importantly for the open-world correction, measured an Open Images negative false-accept rate of **0.0873**. The tradeoff is now explicit instead of hidden: Open Images positive retention is **0.5951**, so v2.1 is stricter and more honest, but the next detector-quality target is recovering more valid web-style produce without re-opening the non-produce hallucination failure. On the local `C:\Users\abdoe\Desktop\test_img` folder, the car image now returns `unknown / n_a`, the grouped apple image keeps five item-level apple boxes with no full-frame scene box, and the apple freshness smoke images behave as the release story claims.

---

## How to use this story

- **README hero copy** — Acts 1 + 6, condensed to four sentences.
- **Architecture diagram** — Acts 5 + 7, the contract paragraph plus the open-world filtering correction.
- **Thumbnail kicker** — Pick from: _"From closed-set to honest."_ · _"A public model, tested in the open."_ · _"The gap between a benchmark and the web."_

---

## Living document — update protocol

Update this file after any of the following:

- A v2 notebook lands and produces new numbers.
- A real-world test result changes (the five apples re-tested, or new test images added).
- A research decision changes (new backbone considered, new dataset added, scope cut).
- A phase completes or a new phase opens (the acts grow).

Keep prose tone. Past tense for what shipped. Present tense for what's underway. Future tense for what's next. Never collapse an act into bullets — bullets are for the plan file, not the story.
