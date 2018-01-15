from sportorg import config
from sportorg.gui.dialogs.report_dialog import ReportDialog
import codecs
import time
import webbrowser

from sportorg.core.template import get_text_from_file, get_templates
from sportorg.gui.dialogs.file_dialog import get_save_file_name
from sportorg.language import _
from sportorg.models.result.score_calculation import ScoreCalculation


class TeamResultsReportDialog(ReportDialog):
    def apply_changes_impl(self):
        template_path = self.item_template.currentText()

        ScoreCalculation.calculate_scores()
        data = ScoreCalculation.get_team_results_data()
        template = get_text_from_file(template_path, **data)

        file_name = get_save_file_name(_('Save As HTML file'),
                                       _("HTML file (*.html)"), '{}_report'.format(time.strftime("%Y%m%d")))
        if file_name:
            with codecs.open(file_name, 'w', 'utf-8') as file:
                file.write(template)
                file.close()

            # Open file in your browser
            webbrowser.open('file://' + file_name, new=2)

    def init_ui(self):
        super().init_ui()
        self.item_template.clear()
        self.item_template.addItems(get_templates(config.template_dir('team_results')))
