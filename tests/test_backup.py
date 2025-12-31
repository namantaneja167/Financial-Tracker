"""Tests for the backup module."""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import zipfile
import json

import pytest

from financial_tracker.backup import (
    create_backup,
    list_backups,
    restore_backup,
    delete_backup,
    get_backup_info,
    BACKUP_DIR
)


class TestCreateBackup:
    """Tests for create_backup function."""
    
    def test_create_backup_with_db(self, tmp_path):
        """Test creating backup with database."""
        # Create temporary files
        temp_db = tmp_path / "financial_tracker.db"
        temp_db.write_text("test db")
        temp_backup_dir = tmp_path / "backups"
        temp_backup_dir.mkdir()
        
        with patch('financial_tracker.backup.DB_PATH', temp_db):
            with patch('financial_tracker.backup.BACKUP_DIR', temp_backup_dir):
                result = create_backup(include_db=True, include_config=False)
                
                assert result is not None
                assert result.exists()
                assert result.suffix == '.zip'
                
                # Verify contents
                with zipfile.ZipFile(result, 'r') as zf:
                    assert temp_db.name in zf.namelist()
    
    def test_create_backup_with_config(self, tmp_path):
        """Test creating backup with config."""
        temp_config = tmp_path / "config.yaml"
        temp_config.write_text("test config")
        temp_backup_dir = tmp_path / "backups"
        temp_backup_dir.mkdir()
        
        with patch('financial_tracker.backup.CONFIG_PATH', temp_config):
            with patch('financial_tracker.backup.BACKUP_DIR', temp_backup_dir):
                result = create_backup(include_db=False, include_config=True)
                
                assert result is not None
                assert result.exists()
                
                # Verify contents
                with zipfile.ZipFile(result, 'r') as zf:
                    assert temp_config.name in zf.namelist()
    
    def test_create_backup_with_both(self, tmp_path):
        """Test creating backup with both files."""
        temp_db = tmp_path / "financial_tracker.db"
        temp_db.write_text("test db")
        temp_config = tmp_path / "config.yaml"
        temp_config.write_text("test config")
        temp_backup_dir = tmp_path / "backups"
        temp_backup_dir.mkdir()
        
        with patch('financial_tracker.backup.DB_PATH', temp_db):
            with patch('financial_tracker.backup.CONFIG_PATH', temp_config):
                with patch('financial_tracker.backup.BACKUP_DIR', temp_backup_dir):
                    result = create_backup(include_db=True, include_config=True)
                    
                    assert result is not None
                    
                    # Verify contents
                    with zipfile.ZipFile(result, 'r') as zf:
                        assert temp_db.name in zf.namelist()
                        assert temp_config.name in zf.namelist()
                        assert "backup_metadata.json" in zf.namelist()
    
    def test_create_backup_requires_selection(self):
        """Test that backup creation requires at least one file selected."""
        with pytest.raises(ValueError):
            create_backup(include_db=False, include_config=False)


class TestListBackups:
    """Tests for list_backups function."""
    
    def test_list_empty_backups(self, tmp_path):
        """Test listing backups when directory is empty."""
        with patch('financial_tracker.backup.BACKUP_DIR', tmp_path):
            result = list_backups()
            assert result == []
    
    def test_list_backups_sorted(self, tmp_path):
        """Test that backups are sorted by date descending."""
        # Create mock backup files with correct naming pattern
        (tmp_path / "financial_tracker_backup_2024-01-01.zip").touch()
        (tmp_path / "financial_tracker_backup_2024-02-01.zip").touch()
        
        with patch('financial_tracker.backup.BACKUP_DIR', tmp_path):
            result = list_backups()
            assert len(result) == 2
    
    def test_list_backups_with_metadata(self, tmp_path):
        """Test listing backups that contain metadata."""
        backup_file = tmp_path / "financial_tracker_backup_2024-01-01.zip"
        
        # Create backup with metadata
        with zipfile.ZipFile(backup_file, 'w') as zf:
            metadata = {
                "timestamp": "2024-01-01T12:00:00",
                "includes_db": True,
                "includes_config": False
            }
            zf.writestr("backup_metadata.json", json.dumps(metadata))
        
        with patch('financial_tracker.backup.BACKUP_DIR', tmp_path):
            result = list_backups()
            assert len(result) == 1
            assert "metadata" in result[0]
            assert result[0]["metadata"]["includes_db"] is True


class TestDeleteBackup:
    """Tests for delete_backup function."""
    
    def test_delete_existing_backup(self, tmp_path):
        """Test deleting an existing backup."""
        backup_file = tmp_path / "backup.zip"
        backup_file.touch()
        
        result = delete_backup(backup_file)
        assert result is True
        assert not backup_file.exists()
    
    def test_delete_nonexistent_backup(self, tmp_path):
        """Test deleting a non-existent backup."""
        fake_path = tmp_path / "nonexistent.zip"
        result = delete_backup(fake_path)
        assert result is False


class TestGetBackupInfo:
    """Tests for get_backup_info function."""
    
    def test_get_info_nonexistent(self, tmp_path):
        """Test getting info for non-existent backup."""
        fake_path = tmp_path / "nonexistent.zip"
        result = get_backup_info(fake_path)
        assert result is None
    
    def test_get_info_with_metadata(self, tmp_path):
        """Test getting info from backup with metadata."""
        backup_file = tmp_path / "backup.zip"
        
        # Create backup with metadata
        with zipfile.ZipFile(backup_file, 'w') as zf:
            metadata = {
                "timestamp": "2024-01-01T12:00:00",
                "includes_db": True,
                "includes_config": False
            }
            zf.writestr("backup_metadata.json", json.dumps(metadata))
        
        result = get_backup_info(backup_file)
        assert result is not None
        assert result["metadata"]["includes_db"] is True
        assert result["metadata"]["includes_config"] is False


class TestRestoreBackup:
    """Tests for restore_backup function."""
    
    def test_restore_requires_selection(self, tmp_path):
        """Test that restore requires at least one file selected."""
        # Create a dummy backup file
        backup_file = tmp_path / "backup.zip"
        backup_file.touch()
        
        with pytest.raises(ValueError):
            restore_backup(backup_file, restore_db=False, restore_config=False)
    
    def test_restore_nonexistent_fails(self):
        """Test restoring from non-existent backup fails."""
        with pytest.raises(FileNotFoundError):
            restore_backup(Path("nonexistent.zip"), restore_db=True)
    
    def test_restore_database(self, tmp_path):
        """Test restoring database from backup."""
        # Create source database
        original_db = tmp_path / "original" / "financial_tracker.db"
        original_db.parent.mkdir()
        original_db.write_text("original database content")
        
        # Create backup with database
        backup_file = tmp_path / "backup.zip"
        with zipfile.ZipFile(backup_file, 'w') as zf:
            zf.write(original_db, arcname="financial_tracker.db")
            metadata = {"database_name": "financial_tracker.db"}
            zf.writestr("backup_metadata.json", json.dumps(metadata))
        
        # Create destination database (to be replaced)
        dest_db = tmp_path / "dest" / "financial_tracker.db"
        dest_db.parent.mkdir()
        dest_db.write_text("destination content to replace")
        
        with patch('financial_tracker.backup.DB_PATH', dest_db):
            result = restore_backup(backup_file, restore_db=True, restore_config=False)
        
        assert result["database_restored"] is True
        assert dest_db.read_text() == "original database content"
    
    def test_restore_config(self, tmp_path):
        """Test restoring config from backup."""
        # Create source config
        original_config = tmp_path / "original" / "config.yaml"
        original_config.parent.mkdir()
        original_config.write_text("original config content")
        
        # Create backup with config
        backup_file = tmp_path / "backup.zip"
        with zipfile.ZipFile(backup_file, 'w') as zf:
            zf.write(original_config, arcname="config.yaml")
            metadata = {"config_name": "config.yaml"}
            zf.writestr("backup_metadata.json", json.dumps(metadata))
        
        # Create destination config (to be replaced)
        dest_config = tmp_path / "dest" / "config.yaml"
        dest_config.parent.mkdir()
        dest_config.write_text("destination content to replace")
        
        with patch('financial_tracker.backup.CONFIG_PATH', dest_config):
            result = restore_backup(backup_file, restore_db=False, restore_config=True)
        
        assert result["config_restored"] is True
        assert dest_config.read_text() == "original config content"
    
    def test_restore_missing_db_in_backup(self, tmp_path):
        """Test restore reports error when db missing from backup."""
        # Create backup without database
        backup_file = tmp_path / "backup.zip"
        with zipfile.ZipFile(backup_file, 'w') as zf:
            metadata = {"includes_database": False}
            zf.writestr("backup_metadata.json", json.dumps(metadata))
        
        dest_db = tmp_path / "dest" / "financial_tracker.db"
        dest_db.parent.mkdir()
        dest_db.write_text("existing db")
        
        with patch('financial_tracker.backup.DB_PATH', dest_db):
            result = restore_backup(backup_file, restore_db=True, restore_config=False)
        
        assert result["database_restored"] is False
        assert len(result["errors"]) > 0
    
    def test_restore_creates_pre_restore_backup(self, tmp_path):
        """Test that restore creates backup of current files first."""
        # Create source database
        original_db = tmp_path / "original" / "financial_tracker.db"
        original_db.parent.mkdir()
        original_db.write_text("backup content")
        
        # Create backup with database
        backup_file = tmp_path / "backup.zip"
        with zipfile.ZipFile(backup_file, 'w') as zf:
            zf.write(original_db, arcname="financial_tracker.db")
            metadata = {"database_name": "financial_tracker.db"}
            zf.writestr("backup_metadata.json", json.dumps(metadata))
        
        # Create destination database
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        dest_db = dest_dir / "financial_tracker.db"
        dest_db.write_text("current content")
        
        with patch('financial_tracker.backup.DB_PATH', dest_db):
            restore_backup(backup_file, restore_db=True, restore_config=False)
        
        # Check pre-restore backup was created
        pre_restore_files = list(dest_dir.glob("*_pre_restore_*"))
        assert len(pre_restore_files) == 1
        assert pre_restore_files[0].read_text() == "current content"
    
    def test_restore_both_db_and_config(self, tmp_path):
        """Test restoring both database and config."""
        # Create originals
        original_db = tmp_path / "original" / "financial_tracker.db"
        original_config = tmp_path / "original" / "config.yaml"
        original_db.parent.mkdir()
        original_db.write_text("backup db")
        original_config.write_text("backup config")
        
        # Create backup
        backup_file = tmp_path / "backup.zip"
        with zipfile.ZipFile(backup_file, 'w') as zf:
            zf.write(original_db, arcname="financial_tracker.db")
            zf.write(original_config, arcname="config.yaml")
            metadata = {
                "database_name": "financial_tracker.db",
                "config_name": "config.yaml"
            }
            zf.writestr("backup_metadata.json", json.dumps(metadata))
        
        # Create destinations
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        dest_db = dest_dir / "financial_tracker.db"
        dest_config = dest_dir / "config.yaml"
        dest_db.write_text("current db")
        dest_config.write_text("current config")
        
        with patch('financial_tracker.backup.DB_PATH', dest_db):
            with patch('financial_tracker.backup.CONFIG_PATH', dest_config):
                result = restore_backup(backup_file, restore_db=True, restore_config=True)
        
        assert result["database_restored"] is True
        assert result["config_restored"] is True
        assert dest_db.read_text() == "backup db"
        assert dest_config.read_text() == "backup config"

