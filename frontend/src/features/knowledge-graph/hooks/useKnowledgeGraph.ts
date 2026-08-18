import { useState } from "react";


export function useKnowledgeGraph() {

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);


  return {
    loading,
    error,
    setLoading,
    setError,
  };
}