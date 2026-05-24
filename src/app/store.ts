import { configureStore } from '@reduxjs/toolkit';
import { claudeApi } from '../services/claudeApi';

export const store = configureStore({
  reducer: {
    [claudeApi.reducerPath]: claudeApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(claudeApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
