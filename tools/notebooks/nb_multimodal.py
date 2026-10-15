"""Multimodal LLM exercise notebook: image patches, CLIP's contrastive loss, zero-shot classification and image-token cost, in NumPy."""

NBS = []

NBS.append(dict(
    slug='01_images_as_tokens', title='01 · Images as tokens: patches, CLIP loss, zero-shot and token cost', deck='multimodal/01-vision-encoders/', deck_name='Vision encoders: ViT and CLIP', minutes=35,
    goals='ViT-style patchification, CLIP\'s symmetric contrastive loss, zero-shot classification by comparing image and text embeddings, and an image-token cost calculator that reproduces the Claude API\'s published token counts.',
    setup=r'''
def normalize(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)

def log_softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    return z - np.log(np.exp(z).sum(axis=axis, keepdims=True))
''',
    tasks=[
        dict(fn='patchify', title='Cut an image into patches', md=r'''
            A Vision Transformer splits an image of shape (H, W, C) into non-overlapping p × p patches and flattens each into a vector of length p·p·C. Return an array of shape (num_patches, p·p·C), patches in row-major order (left to right, then top to bottom). Assume H and W are multiples of p.''',
             starter=r'''
            def patchify(img, p):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_patchify(f):
                img = np.arange(224 * 224 * 3, dtype=float).reshape(224, 224, 3)
                P = f(img, 16)
                assert P.shape == (196, 768), f"224×224 RGB with 16×16 patches → 196 patches of 768 values, got {P.shape}"
                assert np.array_equal(P[0], img[:16, :16].reshape(-1)), "first patch is the top-left block"
                assert np.array_equal(P[1], img[:16, 16:32].reshape(-1)), "second patch is to its right"
                assert np.array_equal(P[14], img[16:32, :16].reshape(-1)), "patch 14 starts the second row"''',
             solution=r'''
            def patchify_solution(img, p):
                H, W, C = img.shape
                x = img.reshape(H // p, p, W // p, p, C).transpose(0, 2, 1, 3, 4)
                return x.reshape(-1, p * p * C)'''),
        dict(fn='clip_loss', title="CLIP's contrastive loss", md=r'''
            A batch has n images and their n captions, embedded as rows of `img` and `txt`. Normalise both, compute logits `S = img @ txt.T / temperature` (n × n), and return the **mean of two cross-entropies** with the diagonal as the targets: images → captions (rows) and captions → images (columns).''',
             starter=r'''
            def clip_loss(img, txt, temperature=0.07):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_clip_loss(f):
                rng = np.random.default_rng(0)
                E = rng.normal(size=(8, 16))
                aligned = f(E, E + 0.01 * rng.normal(size=E.shape))
                shuffled = f(E, E[rng.permutation(8)])
                assert aligned < 0.05, f"matching pairs should give a near-zero loss, got {aligned:.3f}"
                assert shuffled > 1.0, "mismatched pairs should give a high loss"
                rand = f(rng.normal(size=(64, 512)), rng.normal(size=(64, 512)), temperature=1.0)
                assert abs(rand - np.log(64)) < 0.2, "unrelated embeddings at temperature 1 give about log(n)"''',
             solution=r'''
            def clip_loss_solution(img, txt, temperature=0.07):
                S = normalize(img) @ normalize(txt).T / temperature
                i = np.arange(len(S))
                return float(-(log_softmax(S, 1)[i, i].mean() + log_softmax(S, 0)[i, i].mean()) / 2)'''),
        dict(fn='zero_shot_classify', title='Zero-shot classification', md=r'''
            CLIP classifies without training a classifier: embed a prompt per class ("a photo of a dog", ...) and pick, for each image, the class whose text embedding has the **highest cosine similarity**. `img` is (n, d), `class_txt` is (k, d); return an integer array of n predicted class indices.''',
             starter=r'''
            def zero_shot_classify(img, class_txt):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_zero_shot_classify(f):
                rng = np.random.default_rng(1)
                classes = rng.normal(size=(5, 32))
                labels = rng.integers(0, 5, 200)
                imgs = classes[labels] * rng.uniform(0.5, 3, (200, 1)) + 0.3 * rng.normal(size=(200, 32))
                pred = f(imgs, classes)
                assert pred.shape == (200,) and (pred == labels).mean() > 0.95, "cosine similarity ignores the image embedding's length"''',
             solution=r'''
            def zero_shot_classify_solution(img, class_txt):
                return (normalize(img) @ normalize(class_txt).T).argmax(1)'''),
        dict(fn='visual_tokens', title='What does an image cost?', md=r'''
            The Claude API counts one visual token per 28 × 28-pixel patch: `ceil(w / 28) × ceil(h / 28)`. If the image's long edge exceeds `max_edge` or its token count exceeds `max_tokens`, it is first scaled down, preserving aspect ratio, to the **largest integer size that satisfies both limits** (scale both sides by the same factor and round down). Return `(new_w, new_h, tokens)`. Hint: search the scale factor, e.g. by bisection. (The API\'s own rounding can differ by a pixel; the token counts match its published table.)''',
             starter=r'''
            def visual_tokens(w, h, max_edge=1568, max_tokens=1568):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_visual_tokens(f):
                assert f(200, 200) == (200, 200, 64)
                assert f(1000, 1000) == (1000, 1000, 1296)
                assert f(1920, 1080)[2] == 1560 and f(1920, 1080)[:2] == (1456, 819), f(1920, 1080)
                assert f(1920, 1080, 2576, 4784) == (1920, 1080, 2691), "high-resolution tier keeps a 1080p image"
                assert f(3840, 2160, 2576, 4784) == (2576, 1449, 4784), f(3840, 2160, 2576, 4784)''',
             solution=r'''
            def visual_tokens_solution(w, h, max_edge=1568, max_tokens=1568):
                cost = lambda a, b: math.ceil(a / 28) * math.ceil(b / 28)
                fits = lambda s: max(int(w * s), int(h * s)) <= max_edge and cost(int(w * s), int(h * s)) <= max_tokens
                if fits(1.0):
                    return w, h, cost(w, h)
                lo, hi = 0.0, 1.0
                for _ in range(60):
                    mid = (lo + hi) / 2
                    lo, hi = (mid, hi) if fits(mid) else (lo, mid)
                nw, nh = int(w * lo), int(h * lo)
                return nw, nh, cost(nw, nh)'''),
    ],
    explore_md='Token cost for common image sizes on the standard and high-resolution tiers (the token counts match the API documentation table), and how many visual tokens other connectors hand to the language model.',
    explore=r'''
for w, h in [(200, 200), (1000, 1000), (1092, 1092), (1920, 1080), (2000, 1500), (3840, 2160)]:
    s, hr = visual_tokens_solution(w, h), visual_tokens_solution(w, h, 2576, 4784)
    print(f"{w}x{h}: standard {s[0]}x{s[1]} → {s[2]:5} tokens   high-res {hr[0]}x{hr[1]} → {hr[2]:5} tokens")
print()
print("visual tokens per image handed to the LLM by other designs:")
print("  ViT-B/16 at 224 px:", patchify_solution(np.zeros((224, 224, 3)), 16).shape[0], "patches (+1 class token)")
print("  LLaVA-1.5 (CLIP ViT-L/14 at 336 px):", (336 // 14) ** 2)
print("  Flamingo Perceiver Resampler: 64;  BLIP-2 Q-Former: 32 queries")''',
    takeaways='''
        * Images enter transformers as **patches**: a ViT turns a 224 × 224 image into 196 tokens of 16 × 16 pixels.
        * **CLIP** learns aligned image and text embeddings with a symmetric contrastive loss over a batch, which enables zero-shot classification with text prompts.
        * Visual tokens cost context and money like text tokens; resolution limits cap the cost, and connectors (resamplers, Q-Formers) can compress an image to a few dozen tokens.''',
))
