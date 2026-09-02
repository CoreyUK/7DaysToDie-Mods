// The Eighth Day - AssetBundle builder for Unity.
//
// This is the one step that has to happen on a desktop with Unity installed:
// turning the FBX + baked textures from tools/gen_models.py into the
// .unity3d AssetBundle that 7 Days to Die loads via a Meshfile property.
//
// SETUP (once)
//   1. Find the Unity version the game ships with: right-click
//      7DaysToDie.exe -> Properties -> Details -> "File version" is not it;
//      look at 7DaysToDie_Data/globalgamemanagers, or simply open the game's
//      Player.log, which prints "Initialize engine version: 20xx.x.xxf1" at
//      the top. Install exactly that version via Unity Hub. A bundle built on
//      any other version will silently fail to load.
//   2. New 3D project. Copy this file to Assets/Editor/EighthDayBundleBuilder.cs
//   3. Copy TheEighthDay/Resources/src/* into Assets/EighthDay/Models/ so each
//      asset has its own folder containing the .fbx and its four PNGs.
//
// PER BUILD
//   Eighth Day -> 1. Create Prefabs From Models      (materials + prefabs)
//   Eighth Day -> 2. Build AssetBundle                (-> Assets/../Bundles/eighthday.unity3d)
//
// Then copy eighthday.unity3d to TheEighthDay/Resources/ and wire each block's
// Meshfile in blocks.xml:
//   <property name="Meshfile" value="#@modfolder:Resources/eighthday.unity3d?edBlockBloomery" />
//
// Textures: the generator bakes Roughness; Unity's Standard shader wants
// Smoothness, so this script inverts it into the Metallic map's alpha channel
// at import time. Normal maps are OpenGL convention, which Unity imports as-is.

using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace EighthDay
{
    public static class BundleBuilder
    {
        const string ModelsRoot = "Assets/EighthDay/Models";
        const string PrefabsRoot = "Assets/EighthDay/Prefabs";
        const string BundleName = "eighthday";
        const string OutputDir = "Bundles";

        [MenuItem("Eighth Day/1. Create Prefabs From Models")]
        public static void CreatePrefabs()
        {
            if (!Directory.Exists(ModelsRoot))
            {
                Debug.LogError($"[EighthDay] {ModelsRoot} not found. Copy Resources/src/* there first.");
                return;
            }
            Directory.CreateDirectory(PrefabsRoot);

            var created = 0;
            foreach (var dir in Directory.GetDirectories(ModelsRoot))
            {
                var name = Path.GetFileName(dir);
                var fbxPath = Path.Combine(dir, name + ".fbx").Replace('\\', '/');
                if (!File.Exists(fbxPath))
                {
                    Debug.LogWarning($"[EighthDay] {name}: no {name}.fbx, skipping");
                    continue;
                }

                ConfigureTextures(dir, name);
                var material = BuildMaterial(dir, name);

                var model = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
                if (model == null)
                {
                    Debug.LogError($"[EighthDay] {name}: FBX failed to import");
                    continue;
                }

                var instance = (GameObject)PrefabUtility.InstantiatePrefab(model);
                instance.name = name;
                foreach (var r in instance.GetComponentsInChildren<Renderer>())
                    r.sharedMaterial = material;

                // 7DTD wants a collider on block meshes
                if (instance.GetComponentInChildren<Collider>() == null)
                    foreach (var mf in instance.GetComponentsInChildren<MeshFilter>())
                        mf.gameObject.AddComponent<MeshCollider>().sharedMesh = mf.sharedMesh;

                var prefabPath = $"{PrefabsRoot}/{name}.prefab";
                PrefabUtility.SaveAsPrefabAsset(instance, prefabPath);
                Object.DestroyImmediate(instance);

                var importer = AssetImporter.GetAtPath(prefabPath);
                importer.assetBundleName = BundleName;
                created++;
                Debug.Log($"[EighthDay] prefab: {prefabPath}");
            }

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"[EighthDay] {created} prefab(s) ready. Now run 'Eighth Day -> 2. Build AssetBundle'.");
        }

        [MenuItem("Eighth Day/2. Build AssetBundle")]
        public static void BuildBundle()
        {
            Directory.CreateDirectory(OutputDir);
            var manifest = BuildPipeline.BuildAssetBundles(
                OutputDir,
                BuildAssetBundleOptions.ChunkBasedCompression | BuildAssetBundleOptions.DeterministicAssetBundle,
                BuildTarget.StandaloneWindows64);

            if (manifest == null)
            {
                Debug.LogError("[EighthDay] Bundle build failed - see console.");
                return;
            }

            var src = Path.Combine(OutputDir, BundleName);
            var dst = Path.Combine(OutputDir, BundleName + ".unity3d");
            if (File.Exists(src))
            {
                File.Copy(src, dst, true);
                Debug.Log($"[EighthDay] Built {dst}\n  Copy it to TheEighthDay/Resources/ and wire Meshfile in blocks.xml.\n" +
                          $"  Contents: {string.Join(", ", manifest.GetAllAssetBundles())}");
            }
        }

        // ------------------------------------------------------------------

        static void ConfigureTextures(string dir, string name)
        {
            Set(dir, name, "Normal", t => { t.textureType = TextureImporterType.NormalMap; });
            Set(dir, name, "Roughness", t => { t.sRGBTexture = false; });
            Set(dir, name, "Metallic", t => { t.sRGBTexture = false; });
            Set(dir, name, "BaseColor", t => { t.sRGBTexture = true; });
        }

        static void Set(string dir, string name, string suffix, System.Action<TextureImporter> apply)
        {
            var path = Path.Combine(dir, $"{name}_{suffix}.png").Replace('\\', '/');
            if (!File.Exists(path)) return;
            var imp = AssetImporter.GetAtPath(path) as TextureImporter;
            if (imp == null) return;
            imp.isReadable = true;
            apply(imp);
            imp.SaveAndReimport();
        }

        static Material BuildMaterial(string dir, string name)
        {
            var shader = Shader.Find("Standard");
            var mat = new Material(shader) { name = name + "_mat" };

            var baseColor = Load(dir, name, "BaseColor");
            var normal = Load(dir, name, "Normal");
            var rough = Load(dir, name, "Roughness");
            var metal = Load(dir, name, "Metallic");

            if (baseColor) mat.SetTexture("_MainTex", baseColor);
            if (normal)
            {
                mat.SetTexture("_BumpMap", normal);
                mat.EnableKeyword("_NORMALMAP");
            }

            // Standard shader reads metallic from R and smoothness from A of
            // one texture. Compose it: R = metallic, A = 1 - roughness.
            if (rough && metal)
            {
                var packed = new Texture2D(rough.width, rough.height, TextureFormat.RGBA32, true);
                var rp = rough.GetPixels();
                var mp = metal.GetPixels();
                var outp = new Color[rp.Length];
                for (var i = 0; i < rp.Length; i++)
                    outp[i] = new Color(mp[i].r, 0f, 0f, 1f - rp[i].r);
                packed.SetPixels(outp);
                packed.Apply();
                var packedPath = Path.Combine(dir, $"{name}_MetallicSmoothness.png").Replace('\\', '/');
                File.WriteAllBytes(packedPath, packed.EncodeToPNG());
                AssetDatabase.ImportAsset(packedPath);
                var pimp = AssetImporter.GetAtPath(packedPath) as TextureImporter;
                if (pimp != null) { pimp.sRGBTexture = false; pimp.SaveAndReimport(); }
                mat.SetTexture("_MetallicGlossMap", AssetDatabase.LoadAssetAtPath<Texture2D>(packedPath));
                mat.EnableKeyword("_METALLICGLOSSMAP");
            }

            var matPath = Path.Combine(dir, $"{name}.mat").Replace('\\', '/');
            AssetDatabase.CreateAsset(mat, matPath);
            return AssetDatabase.LoadAssetAtPath<Material>(matPath);
        }

        static Texture2D Load(string dir, string name, string suffix) =>
            AssetDatabase.LoadAssetAtPath<Texture2D>(
                Path.Combine(dir, $"{name}_{suffix}.png").Replace('\\', '/'));
    }
}
