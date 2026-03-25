from flask import Blueprint
from zou.app.utils.api import configure_api_from_blueprint

from zou.app.blueprints.shots.storyboard_resources import (
    StoryboardResource,
    StoryboardReorderResource,
    StoryboardReorderSequencesResource,
    StoryboardSequenceResource,
    StoryboardShotAssignResource,
    StoryboardShotStatusResource,
    StoryboardBatchAssignResource,
    StoryboardTaskStatusesResource,
    StoryboardShotVersionsResource,
    StoryboardShotVersionUploadResource,
    StoryboardShotVersionSetActiveResource,
    StoryboardBatchStatusResource,
    StoryboardBatchDeleteResource,
    StoryboardBatchDownloadResource,
    StoryboardBatchUploadResource,
    StoryboardShotTimingResource,
    StoryboardBatchTimingResource,
)
from zou.app.blueprints.shots.annotation_resources import (
    StoryboardAnnotationResource,
    VideoFrameAnnotationResource,
    AudioMarkerResource,
)
from zou.app.blueprints.shots.review_resources import (
    StoryboardReviewResource,
    StoryboardReviewStatusesResource,
)
from zou.app.blueprints.shots.analysis_resources import (
    StyleAnalysisResource,
    StyleAnalysisResultResource,
    BatchStyleAnalysisResource,
    StyleKeywordTranslateResource,
    StyleConsistencyCheckResource,
    StyleReportExportResource,
)
from zou.app.blueprints.shots.style_lock_resources import (
    StyleLockResource,
    StyleReferenceResource,
)
from zou.app.blueprints.shots.style_template_resources import (
    StyleTemplateListResource,
    StyleTemplateResource,
    StyleTemplateApplyResource,
)
from zou.app.blueprints.shots.prompt_library_resources import (
    PromptLibraryListResource,
    PromptLibraryResource,
    PromptLibraryFavoriteResource,
    PromptLibraryRevertResource,
    PromptLibraryUseResource,
)
from zou.app.blueprints.shots.camera_language_resources import (
    CameraLanguageListResource,
    CameraLanguageResource,
    CameraLanguageInitResource,
)
from zou.app.blueprints.shots.resources import (
    ShotResource,
    ShotsResource,
    AllShotsResource,
    ShotsAndTasksResource,
    ShotAssetsResource,
    ShotPreviewsResource,
    ShotTaskTypesResource,
    ShotTasksResource,
    ShotVersionsResource,
    SceneResource,
    ScenesResource,
    SceneAndTasksResource,
    SceneTasksResource,
    SceneTaskTypesResource,
    SceneShotsResource,
    RemoveShotFromSceneResource,
    ProjectShotsResource,
    ProjectScenesResource,
    ProjectSequencesResource,
    ProjectEpisodesResource,
    ProjectEpisodeStatsResource,
    ProjectEpisodeRetakeStatsResource,
    EpisodeResource,
    EpisodesResource,
    EpisodeShotsResource,
    EpisodeAndTasksResource,
    EpisodeSequencesResource,
    EpisodeTasksResource,
    EpisodeTaskTypesResource,
    SequenceResource,
    SequencesResource,
    SequenceShotsResource,
    SequenceAndTasksResource,
    SequenceScenesResource,
    SequenceTasksResource,
    SequenceTaskTypesResource,
    EpisodeShotTasksResource,
    EpisodeAssetTasksResource,
    SequenceShotTasksResource,
    ProjectQuotasResource,
    ProjectPersonQuotasResource,
    SetShotsFramesResource,
)

routes = [
    ("/data/shots", AllShotsResource),
    ("/data/shots/all", ShotsResource),
    ("/data/shots/with-tasks", ShotsAndTasksResource),
    ("/data/shots/<shot_id>", ShotResource),
    ("/data/shots/<shot_id>/assets", ShotAssetsResource),
    ("/data/shots/<shot_id>/task-types", ShotTaskTypesResource),
    ("/data/shots/<shot_id>/tasks", ShotTasksResource),
    ("/data/shots/<shot_id>/preview-files", ShotPreviewsResource),
    ("/data/shots/<shot_id>/versions", ShotVersionsResource),
    ("/data/scenes/all", ScenesResource),
    ("/data/scenes/with-tasks", SceneAndTasksResource),
    ("/data/scenes/<scene_id>", SceneResource),
    ("/data/scenes/<scene_id>/tasks", SceneTasksResource),
    ("/data/scenes/<scene_id>/task-types", SceneTaskTypesResource),
    ("/data/scenes/<scene_id>/shots", SceneShotsResource),
    ("/data/scenes/<scene_id>/shots/<shot_id>", RemoveShotFromSceneResource),
    ("/data/episodes", EpisodesResource),
    ("/data/episodes/with-tasks", EpisodeAndTasksResource),
    ("/data/episodes/<episode_id>", EpisodeResource),
    ("/data/episodes/<episode_id>/shots", EpisodeShotsResource),
    ("/data/episodes/<episode_id>/sequences", EpisodeSequencesResource),
    ("/data/episodes/<episode_id>/tasks", EpisodeTasksResource),
    ("/data/episodes/<episode_id>/task-types", EpisodeTaskTypesResource),
    ("/data/episodes/<episode_id>/shot-tasks", EpisodeShotTasksResource),
    ("/data/episodes/<episode_id>/asset-tasks", EpisodeAssetTasksResource),
    ("/data/sequences", SequencesResource),
    ("/data/sequences/with-tasks", SequenceAndTasksResource),
    ("/data/sequences/<sequence_id>", SequenceResource),
    ("/data/sequences/<sequence_id>/shots", SequenceShotsResource),
    ("/data/sequences/<sequence_id>/scenes", SequenceScenesResource),
    ("/data/sequences/<sequence_id>/tasks", SequenceTasksResource),
    ("/data/sequences/<sequence_id>/task-types", SequenceTaskTypesResource),
    ("/data/sequences/<sequence_id>/shot-tasks", SequenceShotTasksResource),
    ("/data/projects/<project_id>/shots", ProjectShotsResource),
    ("/data/projects/<project_id>/scenes", ProjectScenesResource),
    ("/data/projects/<project_id>/sequences", ProjectSequencesResource),
    ("/data/projects/<project_id>/episodes", ProjectEpisodesResource),
    (
        "/data/projects/<project_id>/episodes/stats",
        ProjectEpisodeStatsResource,
    ),
    (
        "/data/projects/<project_id>/episodes/retake-stats",
        ProjectEpisodeRetakeStatsResource,
    ),
    (
        "/data/projects/<project_id>/quotas/<task_type_id>",
        ProjectQuotasResource,
    ),
    (
        "/data/projects/<project_id>/quotas/persons/<person_id>",
        ProjectPersonQuotasResource,
    ),
    (
        "/actions/projects/<project_id>/task-types/<task_type_id>/set-shot-nb-frames",
        SetShotsFramesResource,
    ),
    ("/data/projects/<project_id>/storyboard", StoryboardResource),
    (
        "/data/projects/<project_id>/storyboard/reorder",
        StoryboardReorderResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/assign",
        StoryboardShotAssignResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/status",
        StoryboardShotStatusResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/batch-assign",
        StoryboardBatchAssignResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/task-statuses",
        StoryboardTaskStatusesResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/reorder-sequences",
        StoryboardReorderSequencesResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/sequences",
        StoryboardSequenceResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/sequences/<sequence_id>",
        StoryboardSequenceResource,
        "storyboardsequencedetail",
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/versions",
        StoryboardShotVersionsResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/versions/upload",
        StoryboardShotVersionUploadResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/versions/set-active",
        StoryboardShotVersionSetActiveResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/batch-status",
        StoryboardBatchStatusResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/batch-delete",
        StoryboardBatchDeleteResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/batch-download",
        StoryboardBatchDownloadResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/batch-upload",
        StoryboardBatchUploadResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/timing",
        StoryboardShotTimingResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/batch-timing",
        StoryboardBatchTimingResource,
    ),
    ("/data/shots/<shot_id>/annotations", StoryboardAnnotationResource),
    (
        "/data/shots/<shot_id>/annotations/frames",
        VideoFrameAnnotationResource,
    ),
    (
        "/data/shots/<shot_id>/annotations/frames/<int:frame_number>",
        VideoFrameAnnotationResource,
        "videoframeannotationdetail",
    ),
    (
        "/data/shots/<shot_id>/annotations/audio-markers",
        AudioMarkerResource,
    ),
    (
        "/data/shots/<shot_id>/annotations/audio-markers/<int:marker_index>",
        AudioMarkerResource,
        "audiomarkerdetail",
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/reviews",
        StoryboardReviewResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/review-statuses",
        StoryboardReviewStatusesResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/analyze",
        StyleAnalysisResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/analysis",
        StyleAnalysisResultResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/batch-analyze",
        BatchStyleAnalysisResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/translate-keywords",
        StyleKeywordTranslateResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/shots/<shot_id>/consistency",
        StyleConsistencyCheckResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/style-report",
        StyleReportExportResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/style-lock",
        StyleLockResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/style-references",
        StyleReferenceResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/style-references/<preview_file_id>",
        StyleReferenceResource,
        "stylereferencedetail",
    ),
    (
        "/data/projects/<project_id>/storyboard/style-templates",
        StyleTemplateListResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/style-templates/<template_id>",
        StyleTemplateResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/style-templates/<template_id>/apply",
        StyleTemplateApplyResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/prompts",
        PromptLibraryListResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/prompts/<prompt_id>",
        PromptLibraryResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/prompts/<prompt_id>/favorite",
        PromptLibraryFavoriteResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/prompts/<prompt_id>/revert",
        PromptLibraryRevertResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/prompts/<prompt_id>/use",
        PromptLibraryUseResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/camera-language",
        CameraLanguageListResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/camera-language/init",
        CameraLanguageInitResource,
    ),
    (
        "/data/projects/<project_id>/storyboard/camera-language/<term_id>",
        CameraLanguageResource,
    ),
]


blueprint = Blueprint("shots", "shots")
api = configure_api_from_blueprint(blueprint, routes)
