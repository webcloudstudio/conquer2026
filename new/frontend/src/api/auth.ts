import { api } from "./client";
import type { User } from "../types";

export async function register(username: string, email: string, password: string): Promise<User> {
  const { data } = await api.post<User>("/auth/register", { username, email, password });
  return data;
}

export async function login(username: string, password: string): Promise<string> {
  const params = new URLSearchParams({ username, password });
  const { data } = await api.post<{ access_token: string }>("/auth/login", params, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data.access_token;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}
