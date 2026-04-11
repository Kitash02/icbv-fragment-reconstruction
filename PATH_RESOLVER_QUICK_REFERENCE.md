# Path Resolver Quick Reference

## Import
```python
import sys
sys.path.insert(0, 'src')
import path_resolver
```

## Detection
```python
path_resolver.is_frozen()  # True if .exe, False if dev
```

## Initialization
```python
path_resolver.ensure_user_directories()  # Create output/, logs/, temp/
```

## Read-Only Resources (Bundled with App)
```python
path_resolver.get_bundle_root()              # App root directory
path_resolver.get_resource_path("config")    # Any bundled resource
path_resolver.get_config_file("settings.json")  # config/settings.json
path_resolver.get_sample_data_dir()          # data/sample/
path_resolver.get_data_dir()                 # data/
```

## Writable Directories (User Data)
```python
path_resolver.get_output_dir()   # Reconstruction results
path_resolver.get_log_dir()      # Log files
path_resolver.get_temp_dir()     # Temporary processing files
path_resolver.get_user_base_dir()  # Base for all user data
```

## Other
```python
path_resolver.get_executable_dir()     # Where .exe or script lives
path_resolver.get_path_diagnostics()   # Dict with debug info
path_resolver.print_diagnostics()      # Print formatted diagnostics
```

## Common Patterns

### Load Configuration
```python
config_path = path_resolver.get_config_file("settings.json")
with open(config_path) as f:
    config = json.load(f)
```

### Save Output
```python
output_dir = path_resolver.get_output_dir()
result_path = output_dir / f"result_{timestamp}.png"
cv2.imwrite(str(result_path), image)
```

### Setup Logging
```python
log_dir = path_resolver.get_log_dir()
log_file = log_dir / f"run_{timestamp}.log"
logging.basicConfig(filename=str(log_file), level=logging.INFO)
```

### Load Sample Data
```python
sample_dir = path_resolver.get_sample_data_dir()
for img_path in sample_dir.glob("*.png"):
    image = cv2.imread(str(img_path))
```

## Development vs Frozen Behavior

| Function | Dev Mode | Frozen Mode (.exe) |
|----------|----------|-------------------|
| `get_bundle_root()` | Project root | Temp extraction folder |
| `get_user_base_dir()` | Project root | ~/Documents/ICBV_FragmentReconstruction/ |
| `get_output_dir()` | project/output/ | ~/Documents/.../output/ |
| `get_log_dir()` | project/logs/ | ~/Documents/.../logs/ |
| `get_config_file()` | project/config/*.json | temp/config/*.json (read-only) |

## Key Points

- All functions return `pathlib.Path` objects
- Writable directories are auto-created
- Use `/` operator to join paths: `dir / "file.txt"`
- Convert to string for APIs that need it: `str(path)`
- Check existence: `path.exists()`
- Resources are read-only in frozen mode
- User directories persist after app closes

## Testing
```bash
python test_path_resolver.py          # Run tests
python src/path_resolver.py           # Print diagnostics
```

## Documentation
See `docs/path_resolver_documentation.md` for full API reference and examples.
