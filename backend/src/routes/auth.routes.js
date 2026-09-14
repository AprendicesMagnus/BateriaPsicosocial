const { Router } = require("express");
const controller = require("../controllers/auth.controller");
const { requireAuth } = require("../middleware/auth");
const asyncHandler = require("../utils/asyncHandler");

const router = Router();

router.post("/register", asyncHandler(controller.register));
router.post("/verify-email", asyncHandler(controller.verifyEmail));
router.post("/resend-code", asyncHandler(controller.resendCode));
router.post("/login", asyncHandler(controller.login));
router.post("/forgot-password", asyncHandler(controller.forgotPassword));
router.post("/verify-reset-code", asyncHandler(controller.verifyResetCode));
router.post("/reset-password", asyncHandler(controller.resetPassword));
router.get("/me", requireAuth, asyncHandler(controller.me));

module.exports = router;
