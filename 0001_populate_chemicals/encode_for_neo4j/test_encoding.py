from unittest import TestCase
import numpy as np
from .main import encode2neo4j


class TestEncoding4neo4j(TestCase):
    def test_perfect_input(self):
        string = '-(dithiodi-2,1-ethanediyl)bis[3-bromo-4-hydroxy-a-(hydroxyimino)-benzenepropanamide'
        expected_result = '-(dithiodi-2,1-ethanediyl)bis[3-bromo-4-hydroxy-a-(hydroxyimino)-benzenepropanamide'
        result = encode2neo4j(string)
        
        self.assertEqual(result, expected_result)

    def test_escape_characters(self):
        string = '4,4\',4\\"-trimethoxytrityl chloride'
        expected_result = '"4,4\',4\"-trimethoxytrityl chloride"'
        result = encode2neo4j(string)
        
        self.assertEqual(result, expected_result)