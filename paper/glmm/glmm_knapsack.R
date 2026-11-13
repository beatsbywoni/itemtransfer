# Mixed-model check for the knapsack example (added after review).
# Logistic mixed models with crossed random intercepts for participants and items (lme4::glmer).
# Usage:  Rscript glmm_knapsack.R /path/to/data_proc/trials_harmonized.csv
# Output: glmm_knapsack_slopes.csv, glmm_knapsack_ratios.csv, glmm_knapsack_log.txt (in the working directory)
suppressPackageStartupMessages(library(lme4))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) stop("Give the path to trials_harmonized.csv as the first argument.")
t0 <- Sys.time()
d <- read.csv(args[1], stringsAsFactors = FALSE)
d <- d[d$variant == "decision" & !(is.na(d$no_response) == FALSE & d$no_response == 1), ]
d$sample_name <- NA
d$sample_name[d$dataset == "K2"] <- "Franco 2021"
d$sample_name[d$dataset == "K4"] <- "Franco 2024"
d$sample_name[d$dataset == "K5"] <- "Doroc 2025"
d$sample_name[d$dataset == "K7" & d$sample == "main"] <- "Lu 2025 main"
d <- d[!is.na(d$sample_name), ]
d$family <- ifelse(d$sample_name %in% c("Franco 2021", "Franco 2024"), "Franco",
                   ifelse(d$sample_name == "Doroc 2025", "Doroc", "Lu"))
d$pid <- paste(d$sample_name, d$participant)
d$item <- d$hash_full
d$correct <- as.integer(d$correct)
cat("responses:", nrow(d), " participants:", length(unique(d$pid)), " items:", length(unique(d$item)), "\n")
print(table(d$sample_name))

ctrl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
slopes <- list(); ratios <- list()
for (m in c("ic", "tcc")) {
  d$x <- d[[m]]
  # (1) one slope per family, conditional (mixed model) and marginal (ordinary logistic regression)
  f1 <- glmer(correct ~ 0 + sample_name + family:x + (1 | pid) + (1 | item), data = d, family = binomial, control = ctrl)
  f0 <- glmer(correct ~ 0 + sample_name + x + (1 | pid) + (1 | item), data = d, family = binomial, control = ctrl)
  g1 <- glm(correct ~ 0 + sample_name + family:x, data = d, family = binomial)
  lrt <- anova(f0, f1)
  co <- summary(f1)$coefficients; vc <- as.data.frame(VarCorr(f1))
  for (fam in c("Franco", "Doroc", "Lu")) {
    r <- paste0("family", fam, ":x")
    slopes[[length(slopes) + 1]] <- data.frame(measure = m, family = fam,
      conditional_slope = co[r, "Estimate"], conditional_se = co[r, "Std. Error"],
      marginal_slope = coef(g1)[r],
      participant_sd = vc$sdcor[vc$grp == "pid"], item_sd = vc$sdcor[vc$grp == "item"],
      lrt_chisq_equal_slopes = lrt$Chisq[2], lrt_df = lrt$Df[2], lrt_p = lrt$`Pr(>Chisq)`[2],
      singular = isSingular(f1), row.names = NULL)
  }
  # (2) for each held-out family: its slope relative to the slope of the other two families
  for (fam in c("Franco", "Doroc", "Lu")) {
    d$held <- as.numeric(d$family == fam)
    d$x_held <- d$x * d$held; d$x_train <- d$x * (1 - d$held)
    fr <- glmer(correct ~ 0 + sample_name + x_train + x_held + (1 | pid) + (1 | item), data = d, family = binomial, control = ctrl)
    gr <- glm(correct ~ 0 + sample_name + x_train + x_held, data = d, family = binomial)
    b <- fixef(fr); V <- as.matrix(vcov(fr))
    ratio <- b["x_held"] / b["x_train"]
    # delta-method standard error of the ratio
    g <- c(-b["x_held"] / b["x_train"]^2, 1 / b["x_train"])
    se <- sqrt(as.numeric(t(g) %*% V[c("x_train", "x_held"), c("x_train", "x_held")] %*% g))
    ratios[[length(ratios) + 1]] <- data.frame(measure = m, heldout_family = fam,
      conditional_train_slope = b["x_train"], conditional_heldout_slope = b["x_held"],
      conditional_ratio = ratio, conditional_ratio_lo = ratio - 1.96 * se, conditional_ratio_hi = ratio + 1.96 * se,
      marginal_ratio = coef(gr)["x_held"] / coef(gr)["x_train"], row.names = NULL)
  }
}
slopes <- do.call(rbind, slopes); ratios <- do.call(rbind, ratios)
write.csv(slopes, "glmm_knapsack_slopes.csv", row.names = FALSE)
write.csv(ratios, "glmm_knapsack_ratios.csv", row.names = FALSE)
print(slopes, digits = 3); print(ratios, digits = 3)
writeLines(c(paste("R", R.version.string), paste("lme4", as.character(packageVersion("lme4"))),
             paste("responses", nrow(d)), paste("minutes", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1))),
           "glmm_knapsack_log.txt")
cat("done\n")
