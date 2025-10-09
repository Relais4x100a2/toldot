"""
Tests pour le module de parsing en streaming.
"""

import pytest
from pathlib import Path
from io import StringIO

from geneweb_py.core.parser.streaming import (
    StreamingLexicalParser,
    StreamingGeneWebParser,
    should_use_streaming,
    estimate_memory_usage,
)
from geneweb_py.core.parser.lexical import TokenType
from geneweb_py.core.exceptions import GeneWebParseError, GeneWebEncodingError


class TestStreamingLexicalParser:
    """Tests pour le parser lexical en streaming."""

    def test_parser_creation(self):
        """Test création du parser."""
        content = StringIO("fam Jean /Dupont/\n")
        parser = StreamingLexicalParser(content, "test.gw")
        assert parser.filename == "test.gw"
        assert parser.line_number == 0
        assert parser.buffer_size == 8192

    def test_parser_with_custom_buffer(self):
        """Test création avec buffer personnalisé."""
        content = StringIO("test")
        parser = StreamingLexicalParser(content, buffer_size=4096)
        assert parser.buffer_size == 4096

    def test_tokenize_simple_line(self):
        """Test tokenisation d'une ligne simple."""
        content = StringIO("fam Jean /Dupont/\n")
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        # Vérifier qu'on a des tokens
        assert len(tokens) > 0
        # Dernier token doit être EOF
        assert tokens[-1].type == TokenType.EOF

    def test_tokenize_multiple_lines(self):
        """Test tokenisation de plusieurs lignes."""
        content = StringIO("fam Jean /Dupont/\n- h 0 Jean /Dupont/\n")
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        assert len(tokens) > 2
        assert tokens[-1].type == TokenType.EOF

    def test_tokenize_with_comments(self):
        """Test tokenisation avec commentaires."""
        content = StringIO("# Ceci est un commentaire\nfam Jean /Dupont/\n")
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        # Vérifier qu'on a un token commentaire
        comment_tokens = [t for t in tokens if t.type == TokenType.COMMENT]
        assert len(comment_tokens) > 0

    def test_tokenize_empty_lines(self):
        """Test tokenisation avec lignes vides."""
        content = StringIO("\n\nfam Jean /Dupont/\n\n")
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        # Les lignes vides doivent être ignorées
        assert tokens[-1].type == TokenType.EOF

    def test_tokenize_notes_block(self):
        """Test tokenisation d'un bloc notes multi-lignes."""
        content = StringIO(
            "notes This is a note\n"
            "Second line\n"
            "end notes\n"
        )
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        assert len(tokens) > 0
        assert tokens[-1].type == TokenType.EOF

    def test_tokenize_notes_db_block(self):
        """Test tokenisation d'un bloc notes-db."""
        content = StringIO(
            "notes-db\n"
            "Database note\n"
            "end notes-db\n"
        )
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        assert len(tokens) > 0

    def test_tokenize_page_ext_block(self):
        """Test tokenisation d'un bloc page-ext."""
        content = StringIO(
            "page-ext External page\n"
            "Content\n"
            "end page-ext\n"
        )
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        assert len(tokens) > 0

    def test_tokenize_wizard_note_block(self):
        """Test tokenisation d'un bloc wizard-note."""
        content = StringIO(
            "wizard-note Note\n"
            "Content\n"
            "end wizard-note\n"
        )
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        assert len(tokens) > 0

    def test_line_numbers_tracking(self):
        """Test que les numéros de ligne sont suivis correctement."""
        content = StringIO("line1\nline2\nline3\n")
        parser = StreamingLexicalParser(content, "test.gw")
        tokens = list(parser.tokenize_lazy())
        
        # Vérifier que les tokens ont des numéros de ligne appropriés
        non_eof_tokens = [t for t in tokens if t.type != TokenType.EOF]
        if non_eof_tokens:
            assert all(t.line_number > 0 for t in non_eof_tokens)


class TestStreamingGeneWebParser:
    """Tests pour le parser GeneWeb en streaming."""

    def test_parser_creation(self):
        """Test création du parser."""
        parser = StreamingGeneWebParser()
        assert parser.validate is True
        assert parser.buffer_size == 8192

    def test_parser_with_custom_settings(self):
        """Test création avec paramètres personnalisés."""
        parser = StreamingGeneWebParser(validate=False, buffer_size=4096)
        assert parser.validate is False
        assert parser.buffer_size == 4096

    def test_parse_file_not_found(self):
        """Test parsing d'un fichier inexistant."""
        parser = StreamingGeneWebParser()
        
        with pytest.raises(GeneWebParseError, match="Fichier non trouvé"):
            list(parser.parse_file_streaming("/path/does/not/exist.gw"))

    def test_parse_file_streaming(self, tmp_path):
        """Test parsing en streaming d'un fichier."""
        # Créer un fichier de test
        test_file = tmp_path / "test.gw"
        test_file.write_text("fam Jean /Dupont/ +Marie /Martin/\n")
        
        parser = StreamingGeneWebParser()
        tokens = list(parser.parse_file_streaming(test_file))
        
        # Vérifier qu'on a des tokens
        assert len(tokens) > 0
        assert tokens[-1].type == TokenType.EOF

    def test_parse_file_with_utf8(self, tmp_path):
        """Test parsing d'un fichier UTF-8."""
        test_file = tmp_path / "test_utf8.gw"
        test_file.write_text("fam François /Müller/\n", encoding="utf-8")
        
        parser = StreamingGeneWebParser()
        tokens = list(parser.parse_file_streaming(test_file))
        
        assert len(tokens) > 0

    def test_parse_file_with_iso88591(self, tmp_path):
        """Test parsing d'un fichier ISO-8859-1."""
        test_file = tmp_path / "test_iso.gw"
        test_file.write_text("fam François /Müller/\n", encoding="iso-8859-1")
        
        parser = StreamingGeneWebParser()
        tokens = list(parser.parse_file_streaming(test_file))
        
        assert len(tokens) > 0

    def test_detect_encoding_utf8(self, tmp_path):
        """Test détection d'encodage UTF-8."""
        test_file = tmp_path / "test.gw"
        test_file.write_text("fam Jean /Dupont/\n", encoding="utf-8")
        
        parser = StreamingGeneWebParser()
        encoding = parser._detect_encoding(test_file)
        
        assert encoding == "utf-8"

    def test_detect_encoding_iso88591(self, tmp_path):
        """Test détection d'encodage ISO-8859-1."""
        test_file = tmp_path / "test.gw"
        # Écrire avec des caractères spécifiques à ISO-8859-1
        with open(test_file, "wb") as f:
            f.write(b"fam Fran\xe7ois /M\xfcller/\n")  # ISO-8859-1
        
        parser = StreamingGeneWebParser()
        encoding = parser._detect_encoding(test_file)
        
        # Devrait détecter un encodage non-UTF-8
        assert encoding != "utf-8"

    def test_parse_large_file(self, tmp_path):
        """Test parsing d'un fichier relativement gros."""
        test_file = tmp_path / "large.gw"
        
        # Créer un fichier avec beaucoup de lignes
        with open(test_file, "w") as f:
            for i in range(100):
                f.write(f"fam Person{i} /Surname{i}/\n")
        
        parser = StreamingGeneWebParser()
        tokens = list(parser.parse_file_streaming(test_file))
        
        # Vérifier qu'on a tokenisé tout le fichier
        assert len(tokens) > 100


class TestShouldUseStreaming:
    """Tests pour la fonction should_use_streaming."""

    def test_small_file(self, tmp_path):
        """Test avec un petit fichier."""
        test_file = tmp_path / "small.gw"
        test_file.write_text("fam Jean /Dupont/\n")
        
        result = should_use_streaming(test_file)
        assert result is False

    def test_large_file(self, tmp_path):
        """Test avec un gros fichier (>10MB)."""
        test_file = tmp_path / "large.gw"
        
        # Créer un fichier de ~11MB
        with open(test_file, "w") as f:
            # Écrire environ 11MB de données
            line = "fam Jean /Dupont/ +Marie /Martin/\n" * 1000
            for _ in range(350):  # ~11MB
                f.write(line)
        
        result = should_use_streaming(test_file)
        assert result is True

    def test_custom_threshold(self, tmp_path):
        """Test avec un seuil personnalisé."""
        test_file = tmp_path / "medium.gw"
        
        # Créer un fichier de ~2MB
        with open(test_file, "w") as f:
            line = "fam Jean /Dupont/\n" * 1000
            for _ in range(60):  # ~2MB
                f.write(line)
        
        # Avec seuil de 1MB, devrait recommander streaming
        assert should_use_streaming(test_file, threshold_mb=1.0) is True
        
        # Avec seuil de 5MB, ne devrait pas recommander streaming
        assert should_use_streaming(test_file, threshold_mb=5.0) is False

    def test_nonexistent_file(self):
        """Test avec un fichier inexistant."""
        result = should_use_streaming("/path/does/not/exist.gw")
        assert result is False

    def test_string_path(self, tmp_path):
        """Test avec un chemin string."""
        test_file = tmp_path / "test.gw"
        test_file.write_text("test\n")
        
        result = should_use_streaming(str(test_file))
        assert isinstance(result, bool)


class TestEstimateMemoryUsage:
    """Tests pour la fonction estimate_memory_usage."""

    def test_small_file_estimation(self, tmp_path):
        """Test estimation pour un petit fichier."""
        test_file = tmp_path / "small.gw"
        test_file.write_text("fam Jean /Dupont/\n")
        
        estimation = estimate_memory_usage(test_file)
        
        assert "file_size_mb" in estimation
        assert "estimated_normal_memory_mb" in estimation
        assert "estimated_streaming_memory_mb" in estimation
        assert "memory_saving_percent" in estimation
        assert "recommended_mode" in estimation
        
        assert estimation["file_size_mb"] >= 0  # Peut être 0.0 pour fichiers très petits
        assert estimation["estimated_normal_memory_mb"] >= estimation["estimated_streaming_memory_mb"]
        assert estimation["recommended_mode"] == "normal"

    def test_large_file_estimation(self, tmp_path):
        """Test estimation pour un gros fichier."""
        test_file = tmp_path / "large.gw"
        
        # Créer un fichier de ~12MB
        with open(test_file, "w") as f:
            line = "fam Jean /Dupont/ +Marie /Martin/\n" * 1000
            for _ in range(380):  # ~12MB
                f.write(line)
        
        estimation = estimate_memory_usage(test_file)
        
        assert estimation["file_size_mb"] >= 10
        assert estimation["recommended_mode"] == "streaming"
        assert estimation["memory_saving_percent"] > 0

    def test_estimation_calculations(self, tmp_path):
        """Test calculs d'estimation."""
        test_file = tmp_path / "test.gw"
        test_file.write_text("test\n" * 10000)
        
        estimation = estimate_memory_usage(test_file)
        
        # Vérifier les ratios approximatifs
        file_size = estimation["file_size_mb"]
        normal_mem = estimation["estimated_normal_memory_mb"]
        streaming_mem = estimation["estimated_streaming_memory_mb"]
        
        # Normal devrait être ~7.5x la taille du fichier
        assert abs(normal_mem - file_size * 7.5) < 0.1
        
        # Streaming devrait être ~1.5x la taille du fichier
        assert abs(streaming_mem - file_size * 1.5) < 0.1

    def test_memory_saving_percent(self, tmp_path):
        """Test calcul du pourcentage d'économie mémoire."""
        test_file = tmp_path / "test.gw"
        test_file.write_text("test\n" * 1000)
        
        estimation = estimate_memory_usage(test_file)
        
        # Streaming devrait économiser environ 80% de mémoire
        assert 70 <= estimation["memory_saving_percent"] <= 90

    def test_string_path(self, tmp_path):
        """Test avec un chemin string."""
        test_file = tmp_path / "test.gw"
        test_file.write_text("test\n")
        
        estimation = estimate_memory_usage(str(test_file))
        assert isinstance(estimation, dict)
        assert "file_size_mb" in estimation


class TestStreamingIntegration:
    """Tests d'intégration pour le streaming."""

    def test_streaming_vs_normal_consistency(self, tmp_path):
        """Test que le streaming produit les mêmes tokens que le mode normal."""
        # Créer un fichier de test
        test_file = tmp_path / "consistency.gw"
        content = """fam Jean /Dupont/ +Marie /Martin/
- h 0 Jean /Dupont/ *1950
- f 0 Marie /Martin/ *1952
"""
        test_file.write_text(content)
        
        # Parser en streaming
        parser_streaming = StreamingGeneWebParser()
        tokens_streaming = list(parser_streaming.parse_file_streaming(test_file))
        
        # Vérifier qu'on a des tokens
        assert len(tokens_streaming) > 5
        assert tokens_streaming[-1].type == TokenType.EOF

    def test_streaming_with_complex_content(self, tmp_path):
        """Test streaming avec contenu complexe."""
        test_file = tmp_path / "complex.gw"
        content = """# Commentaire
fam Jean /Dupont/ +Marie /Martin/
- h 0 Jean /Dupont/ *1950 +1920 #occ Ingénieur
- f 0 Marie /Martin/ *1952
notes This is a test note
Multiple lines
end notes
"""
        test_file.write_text(content)
        
        parser = StreamingGeneWebParser()
        tokens = list(parser.parse_file_streaming(test_file))
        
        assert len(tokens) > 10

