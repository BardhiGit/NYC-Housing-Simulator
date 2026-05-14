"use client";
import { create } from "zustand";
import { apiClient } from "../api/client";

interface User { id: string; email: string; name: string; }
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  init: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  init: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("access_token");
    const user = localStorage.getItem("user");
    if (token && user) {
      set({ token, user: JSON.parse(user), isAuthenticated: true });
    }
  },

  login: async (email, password) => {
    const { data } = await apiClient.post("/auth/login", { email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    // Decode user from token payload (base64)
    const payload = JSON.parse(atob(data.access_token.split(".")[1]));
    const user = { id: payload.sub, email, name: email.split("@")[0] };
    localStorage.setItem("user", JSON.stringify(user));
    set({ token: data.access_token, user, isAuthenticated: true });
  },

  register: async (name, email, password) => {
    const { data } = await apiClient.post("/auth/register", { name, email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const payload = JSON.parse(atob(data.access_token.split(".")[1]));
    const user = { id: payload.sub, email, name };
    localStorage.setItem("user", JSON.stringify(user));
    set({ token: data.access_token, user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    set({ user: null, token: null, isAuthenticated: false });
    if (typeof window !== "undefined") window.location.href = "/login";
  },
}));
