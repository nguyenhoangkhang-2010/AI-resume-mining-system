import {
  VectorSearchEmptyState,
  VectorSearchHeader,
  VectorSearchInput,
  VectorSearchResultList,
} from "..";

import { useVectorSearch } from "../hooks/useVectorSearch";

import { useState } from "react";


export function VectorSearchView() {
  const {
    loading,
    error,
    results,
    search,
  } = useVectorSearch();


  const [query, setQuery] =
    useState("");


  const handleSearch = () => {
    search(query);
  };


  if (loading) {
    return (
      <div>
        Searching vectors...
      </div>
    );
  }


  if (error) {
    return (
      <div>
        Failed to search vectors
      </div>
    );
  }


  return (
    <section
      className="
        flex
        flex-col
        gap-6
      "
    >
      <VectorSearchHeader />


      <VectorSearchInput
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
      />


      {results.length === 0 ? (
        <VectorSearchEmptyState />
      ) : (
        <VectorSearchResultList
          results={results}
        />
      )}
    </section>
  );
}