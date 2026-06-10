export type ProcessingStatus = "queued" | "processing" | "processed" | "processing failed";
export type BookType = "common" | "technical";

export type Book = {
  id: string;
  title: string;
  author: string;
  summary: string;
  publication_date: string;
  file_extension: string;
  type: BookType;
  processing_attempts: number;
  processing_status: ProcessingStatus;
  created_at: string;
  updated_at: string;
};

export type BookProcessingProgress = {
  book_id: string;
  status: ProcessingStatus;
  progress: number;
  error?: string;
};

export type BookPayload = {
  title: string;
  author: string;
  summary: string;
  publication_date: string;
};

export type Chat = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: string;
  chat_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type ChatDetail = Chat & {
  messages: ChatMessage[];
};
