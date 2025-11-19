import hashlib
from typing import List, Set

class SimHash:
    """
    SimHash implementation for near-duplicate detection.
    """
    
    def __init__(self, hash_bits: int = 64):
        self.hash_bits = hash_bits
        self.hash_mask = (1 << hash_bits) - 1
    
    def compute(self, text: str) -> int:
        """
        Compute SimHash for text.
        """
        if not text:
            return 0
        
        # Tokenize text
        tokens = self._tokenize(text)
        if not tokens:
            return 0
        
        # Initialize hash vector
        hash_vector = [0] * self.hash_bits
        
        # Process each token
        for token in tokens:
            token_hash = self._hash_token(token)
            for i in range(self.hash_bits):
                if token_hash & (1 << i):
                    hash_vector[i] += 1
                else:
                    hash_vector[i] -= 1
        
        # Generate final hash
        simhash = 0
        for i in range(self.hash_bits):
            if hash_vector[i] > 0:
                simhash |= (1 << i)
        
        return simhash
    
    def similarity(self, hash1: int, hash2: int) -> float:
        """
        Calculate similarity between two SimHashes.
        """
        if hash1 == hash2:
            return 1.0
        
        # Calculate Hamming distance
        hamming_distance = bin(hash1 ^ hash2).count('1')
        
        # Convert to similarity (0-1)
        similarity = 1.0 - (hamming_distance / self.hash_bits)
        return max(0.0, similarity)
    
    def is_duplicate(self, hash1: int, hash2: int, threshold: float = 0.8) -> bool:
        """
        Check if two hashes are duplicates based on threshold.
        """
        return self.similarity(hash1, hash2) >= threshold
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        """
        import re
        # Simple tokenization - split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def _hash_token(self, token: str) -> int:
        """
        Hash a token to a bit vector.
        """
        # Use MD5 hash and convert to integer
        md5_hash = hashlib.md5(token.encode()).hexdigest()
        return int(md5_hash, 16) & self.hash_mask

class DuplicateDetector:
    """
    Duplicate detection using SimHash.
    """
    
    def __init__(self, threshold: float = 0.8):
        self.simhash = SimHash()
        self.threshold = threshold
        self._hashes: Set[int] = set()
    
    def add_document(self, text: str) -> bool:
        """
        Add document and check for duplicates.
        Returns True if document is unique, False if duplicate.
        """
        if not text:
            return True
        
        doc_hash = self.simhash.compute(text)
        
        # Check against existing hashes
        for existing_hash in self._hashes:
            if self.simhash.is_duplicate(doc_hash, existing_hash, self.threshold):
                return False
        
        # Add to set
        self._hashes.add(doc_hash)
        return True
    
    def is_duplicate(self, text: str) -> bool:
        """
        Check if text is a duplicate of existing documents.
        """
        if not text:
            return False
        
        doc_hash = self.simhash.compute(text)
        
        for existing_hash in self._hashes:
            if self.simhash.is_duplicate(doc_hash, existing_hash, self.threshold):
                return True
        
        return False
    
    def get_stats(self) -> dict:
        """
        Get duplicate detection statistics.
        """
        return {
            "total_documents": len(self._hashes),
            "threshold": self.threshold,
            "hash_bits": self.simhash.hash_bits
        }