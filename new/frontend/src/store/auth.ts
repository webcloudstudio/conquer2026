import { create } from "zustand";
import type { User } from "../types";
import { getMe } from "../api/auth";

interface AuthState {
  token: string | null;
  user: User | null;
  setToken: (token: string) => void;
  logout: () => void;
  loadMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("token"),
  user: null,

  setToken: (token) => {
    localStorage.setItem("token", token);
    set({ token });
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ token: null, user: null });
  },

  loadMe: async () => {
    try {
      const user = await getMe();
      set({ user });
    } catch {
      set({ token: null, user: null });
      localStorage.removeItem("token");
    }
  },
}));
