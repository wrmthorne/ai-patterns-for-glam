.PHONY: help render preview publish clean

# Configuration
SPACE_ID := davanstrien/ai-patterns-for-glam
BOOK_DIR := _book

help:
	@echo "Available commands:"
	@echo "  make render     - Render the book locally"
	@echo "  make preview    - Render and preview in browser"
	@echo "  make publish    - Render and upload to Hugging Face Space"
	@echo "  make clean      - Remove rendered files"

render:
	@echo "📖 Rendering book..."
	quarto render

preview:
	@echo "👀 Previewing book..."
	quarto preview

publish: render
	@echo "🚀 Publishing to Hugging Face Space..."
	@if [ ! -d "$(BOOK_DIR)" ]; then \
		echo "❌ Error: $(BOOK_DIR)/ not found"; \
		exit 1; \
	fi
	@python3 -c "from huggingface_hub import HfApi; \
		api = HfApi(); \
		api.upload_folder( \
			folder_path='$(BOOK_DIR)', \
			repo_id='$(SPACE_ID)', \
			repo_type='space', \
			commit_message='Update book from local render' \
		); \
		print('✅ Published to https://huggingface.co/spaces/$(SPACE_ID)')"

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf $(BOOK_DIR)
	rm -rf .quarto
	@echo "✨ Clean!"
