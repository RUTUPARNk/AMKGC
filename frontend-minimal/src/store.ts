import { create } from "zustand";

type SessionState = {
  content: string;
  addToken: (token: string) => void;
  reset: () => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  content: "",
  addToken: (token) =>
    set((state) => ({
      content: state.content + token,
    })),
  reset: () => set({ content: "" }),
}));
