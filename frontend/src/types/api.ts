export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  meta?: {
    count: number;
    total_pages: number;
    current_page: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  errors: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  meta: {
    count: number;
    total_pages: number;
    current_page: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
  };
}
