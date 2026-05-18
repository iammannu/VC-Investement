"use client";
import { authApi } from "./api";
import type { User, TokenResponse } from "@/types";

export function saveTokens(tokens: TokenResponse): void {
  localStorage.setItem("access_token", tokens.access_token);
  localStorage.setItem("refresh_token", tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function hasToken(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("access_token");
}

export async function getCurrentUser(): Promise<User | null> {
  if (!hasToken()) return null;
  try {
    const { data } = await authApi.me();
    return data;
  } catch {
    return null;
  }
}

export async function login(email: string, password: string): Promise<User> {
  const { data: tokens } = await authApi.login(email, password);
  saveTokens(tokens);
  const { data: user } = await authApi.me();
  return user;
}

export async function register(
  email: string,
  password: string,
  full_name?: string
): Promise<User> {
  const { data: tokens } = await authApi.register(email, password, full_name);
  saveTokens(tokens);
  const { data: user } = await authApi.me();
  return user;
}

export function logout(): void {
  clearTokens();
  window.location.href = "/login";
}
