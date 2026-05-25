from statistics import mean


def extract_features(window: list[dict]) -> dict:
    alpha = [x.get("alpha", 0.0) for x in window]
    beta = [x.get("beta", 0.0) for x in window]
    theta = [x.get("theta", 0.0) for x in window]
    beta_alpha = mean(beta) / (mean(alpha) + 1e-9)
    theta_alpha = mean(theta) / (mean(alpha) + 1e-9)
    return {
        "alpha_mean": mean(alpha),
        "beta_mean": mean(beta),
        "theta_mean": mean(theta),
        "beta_alpha_ratio": beta_alpha,
        "theta_alpha_ratio": theta_alpha,
    }
