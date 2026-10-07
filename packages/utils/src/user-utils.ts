import { SignupResult } from "@fiery/types";

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateSignupFields(
  email: string,
  password: string,
  name: string,
): SignupResult {
  if (!email || !password || !name) {
    return {
      success: false,
      error: "Missing required field",
      user: null,
    };
  }
  if (!emailRegex.test(email)) {
    return {
      success: false,
      error: "Malformed email",
      user: null,
    };
  }
  if (password.length < 5) {
    return {
      success: false,
      error: "Malformed password",
      user: null,
    };
  }
  return {
    success: true,
    error: null,
    user: null,
  };
}
