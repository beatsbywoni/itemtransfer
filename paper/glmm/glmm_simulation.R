# Mixed model as a comparator in the simulation study (added after review).
# Data are generated as in the base condition of the article (4 families, 48 items and 40 participants each,
# slope 0.5, item residual SD 0.5, ability SD 0.8, intercept 1). For every data set three analyses are run:
#   glmm: logistic mixed model with crossed random intercepts, slope for the training families and for the
#         held-out family; likelihood-ratio test of equal slopes; ratio held-out / training slope
#   glm:  the same fixed effects without random effects (the marginal slopes of the procedure)
# Usage:  Rscript glmm_simulation.R [replications per scenario, default 200]
# Output: glmm_simulation_raw.csv (one row per data set), glmm_simulation_summary.csv, glmm_simulation_log.txt
# The raw file is written after every scenario, so an interrupted run keeps what is finished.
suppressPackageStartupMessages(library(lme4))
args <- commandArgs(trailingOnly = TRUE)
n_rep <- if (length(args) >= 1) as.integer(args[1]) else 200L
t0 <- Sys.time()
scen <- data.frame(
  scenario = c("same slope", "held-out slope half", "held-out slope twice", "same slope, ability SD 1.6 in held-out family",
               "same slope, item residual SD 1 in held-out family", "no relation, item residual SD 1"),
  b_train = c(0.5, 0.5, 0.5, 0.5, 0.5, 0), b_held = c(0.5, 0.25, 1.0, 0.5, 0.5, 0),
  sd_part_held = c(0.8, 0.8, 0.8, 1.6, 0.8, 0.8), sd_item_train = c(0.5, 0.5, 0.5, 0.5, 0.5, 1),
  sd_item_held = c(0.5, 0.5, 0.5, 0.5, 1, 1), stringsAsFactors = FALSE)
n_fam <- 4; n_items <- 48; n_part <- 40; intercept <- 1
ctrl <- glmerControl(optimizer = "bobyqa", calc.derivs = FALSE)
simulate <- function(s) {
  out <- vector("list", n_fam)
  for (f in seq_len(n_fam)) {
    held <- f == 1
    x <- rnorm(n_items)
    u <- rnorm(n_items, 0, if (held) s$sd_item_held else s$sd_item_train)
    th <- rnorm(n_part, 0, if (held) s$sd_part_held else 0.8)
    b <- if (held) s$b_held else s$b_train
    eta <- outer(th, intercept + b * x + u, "+")
    y <- rbinom(length(eta), 1, plogis(eta))
    out[[f]] <- data.frame(fam = paste0("F", f), pid = paste0("F", f, "p", rep(seq_len(n_part), times = n_items)),
                           item = paste0("F", f, "i", rep(seq_len(n_items), each = n_part)),
                           x = rep(x, each = n_part), held = as.numeric(held), y = y)
  }
  do.call(rbind, out)
}
raw <- list()
for (k in seq_len(nrow(scen))) {
  s <- scen[k, ]
  set.seed(2609 + k)
  for (r in seq_len(n_rep)) {
    d <- simulate(s)
    d$x_held <- d$x * d$held; d$x_train <- d$x * (1 - d$held)
    res <- tryCatch({
      f1 <- suppressMessages(glmer(y ~ 0 + fam + x_train + x_held + (1 | pid) + (1 | item), data = d, family = binomial, control = ctrl, nAGQ = 0))
      f0 <- suppressMessages(glmer(y ~ 0 + fam + x + (1 | pid) + (1 | item), data = d, family = binomial, control = ctrl, nAGQ = 0))
      g1 <- glm(y ~ 0 + fam + x_train + x_held, data = d, family = binomial)
      g0 <- glm(y ~ 0 + fam + x, data = d, family = binomial)
      b <- fixef(f1)
      data.frame(scenario = s$scenario, rep = r,
                 glmm_train = b["x_train"], glmm_held = b["x_held"], glmm_ratio = b["x_held"] / b["x_train"],
                 glmm_p_equal = pchisq(2 * (as.numeric(logLik(f1)) - as.numeric(logLik(f0))), 1, lower.tail = FALSE),
                 glm_train = coef(g1)["x_train"], glm_held = coef(g1)["x_held"], glm_ratio = coef(g1)["x_held"] / coef(g1)["x_train"],
                 glm_p_equal = pchisq(deviance(g0) - deviance(g1), 1, lower.tail = FALSE), row.names = NULL)
    }, error = function(e) NULL)
    if (!is.null(res)) raw[[length(raw) + 1]] <- res
  }
  rawdf <- do.call(rbind, raw)
  write.csv(rawdf, "glmm_simulation_raw.csv", row.names = FALSE)
  cat(format(Sys.time(), "%H:%M"), "finished scenario", k, "of", nrow(scen), ":", s$scenario, "\n")
}
rawdf <- do.call(rbind, raw)
summ <- do.call(rbind, lapply(split(rawdf, rawdf$scenario), function(z) data.frame(
  scenario = z$scenario[1], n = nrow(z),
  glmm_ratio_median = median(z$glmm_ratio), glm_ratio_median = median(z$glm_ratio),
  glmm_train_mean = mean(z$glmm_train), glmm_held_mean = mean(z$glmm_held),
  glm_train_mean = mean(z$glm_train), glm_held_mean = mean(z$glm_held),
  glmm_reject_equal = mean(z$glmm_p_equal < .05), glm_reject_equal = mean(z$glm_p_equal < .05))))
summ <- summ[match(scen$scenario, summ$scenario), ]
write.csv(summ, "glmm_simulation_summary.csv", row.names = FALSE)
print(summ, digits = 3, row.names = FALSE)
writeLines(c(paste("R", R.version.string), paste("lme4", as.character(packageVersion("lme4"))),
             paste("replications per scenario", n_rep), "glmer with nAGQ = 0 (fast approximation), optimiser bobyqa",
             paste("minutes", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1))), "glmm_simulation_log.txt")
cat("done\n")
