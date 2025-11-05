# Backend Comparison

Feature comparison across supported providers and models.

## Summary Table

| Capability | OpenAI Sora-2 | Azure Sora | Google Veo-3 | RunwayML Gen-4 | RunwayML Veo |
|---|---|---|---|---|---|
| Auth | API key | Azure key/CLI | OAuth2 (Vertex AI) | API key | API key |
| Setup | Easy | Medium (enterprise) | Medium/Advanced | Easy | Easy |
| Models | sora-2, sora-2-pro | sora-2, sora-2-pro | veo-3.0, veo-3.1, fast | gen4, gen4_turbo | veo3, veo3.1, veo3.1_fast |
| Ref Images | Multiple | Multiple | Up to 3 | Single only | Up to 3 |
| Duration | Flexible | Flexible | 2–10s | 5 or 10s | 2–10s |
| Stitching | No | No | Yes (3.1) | No | Yes (Veo) |
| Enterprise | No | Yes | No | No | No |
| Pricing | Per-second | Per-second (Azure) | $0.15–$0.40/video | Credits/sec | Credits/sec |

## When to Choose Which

- Sora-2 (OpenAI): simplest setup, flexible durations, high quality
- Azure Sora: enterprise security, RBAC, private endpoints, regional control
- Google Veo-3: seamless stitching, predictable per-video pricing
- Runway Gen-4: fastest prototyping, single-image workflows
- Runway Veo: access Veo without Google Cloud setup; stitching supported

## Model Matrix

| Model | Provider | Speed | Quality | Duration | Stitching |
|---|---|---|---|---|---|
| sora-2 | OpenAI/Azure | Std | High | Flexible | ❌ |
| sora-2-pro | OpenAI/Azure | Std | Very High | Flexible | ❌ |
| veo-3.0-generate-001 | Google | Std | High | 2–10s | ✅ (3.1 models preferred) |
| veo-3.0-fast-generate-001 | Google | Fast | Good | 2–10s | ✅ (3.1 models preferred) |
| veo-3.1-fast-generate-preview | Google | Fast | Excellent | 2–10s | ✅ |
| veo-3.1-generate-preview | Google | Std | Max | 2–10s | ✅ |
| gen4_turbo | Runway | Fast | Good | 5/10s | ❌ |
| gen4 | Runway | Std | High | 5/10s | ❌ |
| veo3.1_fast | Runway (Google) | Fast | Excellent | 2–10s | ✅ |
| veo3.1 | Runway (Google) | Std | Excellent | 2–10s | ✅ |
| veo3 | Runway (Google) | Std | High | 2–10s | ✅ |

## Cost Hints

- Iteration: gen4_turbo (Runway) or veo-3.1_fast (Runway) ≈ cheapest per quality
- Production quality: sora-2-pro, gen4, veo-3.1 (std)
- Long-form sequences: Veo 3.1 + stitching

## Links

- Backends: ../backends/
- CLI options: cli-reference.md
- Auth: authentication.md
